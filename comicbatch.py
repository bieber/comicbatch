#!/usr/bin/env python3

import argparse
import os
import shutil
import zipfile

def get_parser():
    parser = argparse.ArgumentParser(
        prog="comicbatch.py",
        description="Divide CBZ files into PDF compilations with maximum size"
    )
    parser.add_argument('directory', help='Input directory path')
    parser.add_argument(
        '-o',
        '--output',
        help='Prefix for PDF file names',
        default="comic",
    )
    parser.add_argument(
        '-m',
        '--max-file-size',
        help='Maximum PDF file size in bytes',
        default=100_000_000,
    )
    parser.add_argument(
        '-x',
        '--width',
        help='Maximum page width',
        default=1600,
    )
    parser.add_argument(
        '-y',
        '--height',
        help='Maximum page height',
        default=2000
    )
    parser.add_argument('-a', '--author', help='Author metadata')
    parser.add_argument('-t', '--title', help='Title prefix')

    return parser

def init_tmp(temp_path):
    try:
        os.mkdir(temp_path)
    except FileExistsError:
        shutil.rmtree(temp_path)
        os.mkdir(temp_path)
    os.mkdir(os.path.join(temp_path, 'src'))
    os.mkdir(os.path.join(temp_path, 'scaled'))

def extract_zips(directory):
    top_level = list(
        filter(
            lambda s: s.lower().endswith('cbz'),
            os.listdir(directory),
        ),
    )
    top_level.sort(key=lambda s: s.lower())

    i = 0
    for f in top_level:
        os.mkdir(os.path.join(directory, 'tmp/src/%04d' % i))
        z = zipfile.ZipFile(os.path.join(directory, f))
        z.extractall(path=os.path.join(directory, 'tmp/src/%04d' % i))
        i += 1
    return i

def scale_page(src, dst, w, h):
    page = 0
    all_files = []
    for root, _, files in os.walk(src):
        all_files.extend(map(lambda f: os.path.join(root, f), files))
    all_files.sort(key=lambda s: s.split('/')[-1].lower())

    page = 0
    for f in all_files:
        if not f.lower().endswith('jpg'):
            continue
        os.system(
            'convert "%s" -quality 60 -resize %dx%d "%s"' % (
                f,
                w,
                h,
                os.path.join(dst, 'page_%03d.jpg' % page),
            ),
        )
        page += 1

def scale_pages(src, dst, count, w, h):
    for i in range(0, count):
        out_path = os.path.join(dst, '%04d' % i)
        os.mkdir(out_path)
        scale_page(os.path.join(src, '%04d' % i), out_path, w, h)
        print('...%d/%d issues scaled' % (i + 1, count))

def dir_size(path):
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            total += os.path.getsize(os.path.join(root, f))

    return total

def group_issues(src, count, max_size):
    all_groups = []
    current_group = []
    current_group_size = 0

    def rotate_group():
        nonlocal current_group
        nonlocal current_group_size
        all_groups.append(current_group)
        current_group = []
        current_group_size = 0

    def add_issue(i, size):
        nonlocal current_group
        nonlocal current_group_size
        current_group.append(i)
        current_group_size += size

    for i in range(0, count):
        size = dir_size(os.path.join(src, '%04d' % i))
        if size + current_group_size >= max_size:
            rotate_group()
        add_issue(i, size)

    if len(current_group) > 0:
        rotate_group()

    return all_groups

def export_group(indices, temp_path, dst, title, author):
    pages_path = os.path.join(temp_path, 'pages')
    try:
        os.mkdir(pages_path)
    except FileExistsError:
        shutil.rmtree(pages_path)
        os.mkdir(pages_path)

    i = 0
    for issue in indices:
        src = os.path.join(temp_path, 'scaled', '%04d' % issue)
        for page in os.listdir(src):
            shutil.copyfile(
                os.path.join(src, page),
                os.path.join(pages_path, '%03d_%s' % (i, page)),
            )
        i += 1

    all_pages = list(
        map(
            lambda f: '"%s"' % os.path.join(pages_path, f),
            os.listdir(pages_path),
        ),
    )
    all_pages.sort(key=lambda f: f.split('/')[-1])

    optional_args = []
    if title:
        optional_args.append('--title "%s"' % title)
    if author:
        optional_args.append('--author "%s"' % author)
    os.system(
        'img2pdf --output "%s" %s %s' % (
            dst,
            ' '.join(optional_args),
            ' '.join(all_pages),
        ),
    )

args = get_parser().parse_args()
temp_path = os.path.join(args.directory, 'tmp')
init_tmp(temp_path)

print('Extracting pages...')
issue_count = extract_zips(args.directory)
print('Extracted %d issues.' % issue_count)

print('Scaling pages...')
scale_pages(
    os.path.join(temp_path, 'src'),
    os.path.join(temp_path, 'scaled'),
    issue_count,
    args.width,
    args.height,
)
print('Scaled pages.')

print('Grouping issues...')
groups = group_issues(
    os.path.join(temp_path, 'scaled'),
    issue_count,
    args.max_file_size,
)
print('Grouped issues.')

print('Exporting PDFs...')
i = 0
for group in groups:
    export_group(
        group,
        temp_path,
        os.path.join(args.directory, '%s_%03d.pdf' % (args.output, i + 1)),
        '%s %d' % (args.title, i + 1) if args.title else None,
        args.author,
    )
    i += 1
print('Exported %d PDFs.' % len(groups))
shutil.rmtree(os.path.join(args.directory, 'tmp'))
