#!/usr/bin/env python
"""
A trivial code line counter for diff.
"""

import argparse
import re
import sys

class Line:
    def __init__(self, string, line_number):
        # String of the line
        self.string = string
        # Line number. Not be used now.
        self.line_number = line_number

class Diff:
    def __init__(self, filename):
        self.filename = filename
        # List of Line class objects.
        self.add_lines = []
        self.del_lines = []

def diff_per_file(patch):
    """
    Return list of Diff objects.
    """

    # head of svn and git diff
    ptn_index = re.compile(r'(Index: |diff --git )')
    ptn_from  = re.compile(r'--- ')
    ptn_to    = re.compile(r'\+\+\+ ')
    ptn_add   = re.compile(r'\+')
    ptn_del   = re.compile(r'-')
    ptn_range = re.compile(r'@@ -\d+,\d+ \+\d+,\d+ @@')

    diffs = []

    is_code_line = False

    for l in patch.splitlines():
        # Assume the first line matches to ptn_index.
        if ptn_index.match(l):
            if is_code_line:
                # Append diff about previous file if new file found.
                diffs.append(diff)

            is_code_line = False

            # svn -> Index: filename
            # git -> diff --git a/path/to/filename b/path/to/filename
            filename = l.split()[-1].split('/')[-1]

            diff = Diff(filename)
            continue

        m = ptn_range.match(l)
        if m:
            # '@@ -A,B +C,D @@'
            # -> '-A,B +C,D'
            # -> '-A,B', '+C,D'
            # -> 'A,B', 'C,D'
            # -> 'A' 'B', 'C' 'D'
            # -> 'A', 'C'
            from_line, to_line = map(lambda x: int(x[1:].split(',')[0]),
                                     m.group()[3:-3].split())
            is_code_line = True
            continue

        if is_code_line:
            if ptn_add.match(l):
                line = Line(l[1:], to_line) # remove '+'
                diff.add_lines.append(line)
                to_line   += 1
            elif ptn_del.match(l):
                line = Line(l[1:], from_line) # remove '-'
                diff.del_lines.append(line)
                from_line += 1
            else:
                from_line += 1
                to_line   += 1

    diffs.append(diff)
    return diffs

def what_lang(filename):
    """
    Judge what language the file is written by from filename extention.
    """
    langs=[('c|cc|cpp|h', 'c/c++'),
           ('java', 'java'),
           ('sh', 'sh'),
           ('pl', 'perl'),
           ('rb', 'ruby'),
           ('py', 'python'),
           ('xml', 'xml'),
           ('txt|md', 'txt')]

    for lang in langs:
        reg = r'.+\.(' + lang[0] + r')$'
        if re.match(reg, filename):
            return lang[1]

    return 'default'

def is_comment(line_str, lang):
    """
    Judge the line is a comment or not from the head of line.
    Can not check strictly if the line is really a comment.
    """
    if (lang == 'c/c++' or
        lang == 'java'):
        # Assume lines start with '/*', ' *', ' */', '//' are comments.
        #
        # //  ok
        # /*  ok */
        # /*  ok
        #  *  ok
        #     ng
        #  */ ng
        return re.match(r'[ \t]*(/\*| \*| \*/|//)', line_str)

    if (lang == 'sh'   or
        lang == 'perl' or
        lang == 'ruby'):
        return re.match(r'[ \t]*#', line_str)

    if lang == 'python':
        # # ok
        # ''' ok '''
        # """
        # ng
        # """
        return re.match(r'[ \t]*("""|\'\'\'|#)', line_str)

    if lang == 'xml':
        # <!-- ok -->
        # <!-- ok
        # ng
        # -->
        return re.match(r'[ \t]*(<!--|-->)', line_str)

    if lang == 'txt':
        # All lines in a text file are comments.
        return True

    return False

def count_diff(lines, lang):
    """
    return (num_code, num_comments, num_blanks)
    """
    comments = 0
    blanks = 0

    for line in lines:
        if re.match(r'^[ \t]*$', line.string):
            blanks += 1
            continue
        if is_comment(line.string, lang):
            comments += 1
            continue

    code = len(lines) - comments - blanks
    return code, comments, blanks

def parse_args():
    parser = argparse.ArgumentParser(
            description='A trivial code line counter for diff.')
    parser.add_argument('PATCHFILE', nargs='?', default=sys.stdin, type=file,
                        help='a git diff or svn diff file.')
    parser.add_argument('--only-add', action='store_true',
                        help='count only added lines.')
    parser.add_argument('--only-total', action='store_true',
                        help='print only total counts.')
    args = parser.parse_args()

    return args.PATCHFILE, args.only_add, args.only_total

if __name__ == '__main__':
    patchfile, only_add, only_total = parse_args()
    patchdata = patchfile.read()
    diffs = diff_per_file(patchdata)

    if not only_total:
        # The max length of filenames
        fname_len = max(map(lambda diff: len(diff.filename), diffs))
        fname_len = max(fname_len, 5) # For print Total.
    else:
        fname_len = 5

    # 4, 7, 5 are string lengthes of Code, Comment, Blank
    out_format = '{0:<' + str(fname_len) + '} {1} {2:>4} {3:>7} {4:>5}'

    head = out_format.format('Name', ' ', 'Code', 'Comment', 'Blank')

    print head

    hline = '-' * len(head)

    print hline

    total_add_code    = 0
    total_add_comment = 0
    total_add_blank   = 0

    total_del_code    = 0
    total_del_comment = 0
    total_del_blank   = 0

    for diff in diffs:
        lang = what_lang(diff.filename)

        code, comment, blank = count_diff(diff.add_lines, lang)

        total_add_code    += code
        total_add_comment += comment
        total_add_blank   += blank

        if not only_total:
            print out_format.format(diff.filename, '+', code, comment, blank)

        if only_add:
            continue

        code, comment, blank = count_diff(diff.del_lines, lang)

        total_del_code    += code
        total_del_comment += comment
        total_del_blank   += blank

        if not only_total:
            print out_format.format('', '-', code, comment, blank)

    if not only_total:
        print hline

    print out_format.format('Total', '+', total_add_code,
                            total_add_comment, total_add_blank)

    if only_add:
        exit()

    print out_format.format('', '-', total_del_code,
                            total_del_comment, total_del_blank)
