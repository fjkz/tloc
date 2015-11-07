A trivial code line counter for diff.

You can get line counts from git or svn diff.

```
$ git diff | ./tloc.py
Name          Code Comment Blank
--------------------------------
.gitignore  +    2       0     0
            -    0       0     0
LISENCE.txt +    0      16     9
            -    0       0     0
README.md   +    0      19     3
            -    0       0     0
tloc.py     +  115      35    40
            -    0       0     0
--------------------------------
Total       +  117      70    52
            -    0       0     0
```

Note that this tool cannot count the comment lines strictly. Some comment lines
are considered as real lines.
