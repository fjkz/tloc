#!/usr/bin/env python
"""
A trivial code line counter for diff.
"""

import argparse
import re
import sys

def diff_per_file(patch):
    """
    Return [(filename, add_lines, del_lines), ...]
    """

    # head of svn and git diff
    ptn_index = re.compile(r'(Index: |diff --git )')
    ptn_in    = re.compile(r'--- ')
    ptn_out   = re.compile(r'\+\+\+ ')
    ptn_add   = re.compile(r'\+')
    ptn_del   = re.compile(r'-')

    diffs = []
    first_file = True

    filename  = None
    add_lines = None
    del_lines = None

    for l in patch.splitlines():
        # Assume the first line matches to ptn_index.
        if ptn_index.match(l):
            if not first_file:
                diffs.append((filename, add_lines, del_lines))
            else:
                first_file = False

            # svn -> Index: filename
            # git -> diff --git a/path/to/filename b/path/to/filename
            filename = l.split()[-1].split('/')[-1]

            add_lines = []
            del_lines = []
        elif ptn_add.match(l) and not ptn_out.match(l):
            add_lines.append(l[1:])
        elif ptn_del.match(l) and not ptn_in.match(l):
            del_lines.append(l[1:])

    diffs.append((filename, add_lines, del_lines))
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

def is_comment(line, lang):
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
        if re.match(r'[ \t]*(/\*| \*| \*/|//)', line):
            return True

    elif (lang == 'sh'   or
          lang == 'perl' or
          lang == 'ruby'):
        if re.match(r'[ \t]*#', line):
            return True

    elif lang == 'python':
        # # ok
        # ''' ok '''
        # """
        # ng
        # """
        if re.match(r'[ \t]*("""|\'\'\'|#)', line):
            return True

    elif lang == 'xml':
        # <!-- ok -->
        # <!-- ok
        # ng
        # -->
        if re.match(r'[ \t]*(<!--|-->)', line):
            return True

    elif lang == 'txt':
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
        if re.match(r'^[ \t]*$', line):
            blanks += 1
            continue
        if is_comment(line, lang):
            comments += 1
            continue

    code = len(lines) - comments - blanks
    return code, comments, blanks

def parse_args():
    parser = argparse.ArgumentParser(
            description='A trivial code line counter for diff.')
    parser.add_argument('PATCHFILE', nargs='?', default=sys.stdin, type=file,
                        help='a git diff or svn diff file.')
    args = parser.parse_args()
    patchfile = args.PATCHFILE
    return patchfile

if __name__ == '__main__':
    patchfile = parse_args()
    patchdata = patchfile.read()
    diffs = diff_per_file(patchdata)

    # The max length of filenames
    fname_len = max(map(lambda x: len(x[0]), diffs))
    fname_len = max(fname_len, 5) # For print Total.

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
        filename  = diff[0]
        add_lines = diff[1]
        del_lines = diff[2]

        lang = what_lang(filename)

        code, comment, blank = count_diff(add_lines, lang)

        total_add_code    += code
        total_add_comment += comment
        total_add_blank   += blank

        print out_format.format(filename, '+', code, comment, blank)

        code, comment, blank = count_diff(del_lines, lang)

        total_del_code    += code
        total_del_comment += comment
        total_del_blank   += blank

        print out_format.format('', '-', code, comment, blank)

    print hline

    print out_format.format('Total', '+', total_add_code,
                            total_add_comment, total_add_blank)
    print out_format.format('', '-', total_del_code,
                            total_del_comment, total_del_blank)
