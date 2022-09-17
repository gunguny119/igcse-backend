import os
from PIL import Image

import numpy as np


def process_pdf(images, bucket, selected_subject, selected_topics, component, ms=False):
    selected_topic_index = sorted(
        [int(topic.split(' ')[0].replace('.', '')) for topic in selected_topics])
    selected_topic_index = [str(i) for i in selected_topic_index]

    if ms:
        base_dir = 'marking_schemes'

    else:
        base_dir = 'generated_papers'
    if selected_subject != "chemistry":
        base_dir = f'{base_dir}/{selected_subject}'
    if not os.path.isdir(base_dir):
        os.makedirs(base_dir)

    pdf_file_path = f'{base_dir}/component{component}_{"-".join(selected_topic_index)}.pdf'
    real_files, idx = download_images(images, bucket)
    convert_to_pdf(real_files, pdf_file_path, ms=ms)
    upload_pdf(pdf_file_path, bucket)

    return pdf_file_path, len(real_files), idx


def download_images(images, bucket):
    real_files = []
    ignore_idx = []
    for idx, filename in enumerate(images):  # screenshots/year/month/component/q1
        if 'component2' in filename:
            real_file = filename + '.png'
            blob = bucket.blob(real_file)
            if not blob.exists():
                ignore_idx.append(idx)
                continue
            os.makedirs(os.path.dirname(real_file), exist_ok=True)
            blob.download_to_filename(real_file)
            real_files.append(real_file)
        else:
            i = 1
            while True:
                real_file = f'{filename}_p{i}.png'
                blob = bucket.blob(real_file)
                if not blob.exists():
                    if i == 1:
                        ignore_idx.append(idx)
                    break
                os.makedirs(os.path.dirname(real_file), exist_ok=True)
                blob.download_to_filename(real_file)
                real_files.append(real_file)
                i += 1

    idx = np.ones(len(images)).astype(bool)
    idx[ignore_idx] = False

    return real_files, idx


def merge_pages(images, size=(1653, 2339)):
    pages = []
    first = images[0]
    for img in images[1:]:
        merged_height = first.size[1] + img.size[1] + 100
        if merged_height <= size[1]:
            first_arr = np.array(first)[:, :size[0]]
            first_arr = np.pad(first_arr,
                               ((0, 0), (0, size[0] - first_arr.shape[1]), (0, 0)),
                               constant_values=255),
            first = np.concatenate([
                first_arr,
                np.full((100, size[0], 3), 255, dtype=np.uint8),
                np.pad(np.array(img)[:, :size[0]],
                       ((0, 0), (0, size[0] - first.size[0]), (0, 0)),
                       constant_values=255)
            ])
            first = Image.fromarray(first, 'RGB')

        else:
            if first.size[1] < size[1]:
                # make 1 full page
                first_arr = np.array(first)[:, :size[0]]
                first_arr = np.pad(first_arr,
                                   ((0, 0), (0, size[0] - first_arr.shape[1]), (0, 0)),
                                   constant_values=255)
                first = np.concatenate([
                    first_arr,
                    np.full((size[1] - first.size[1], size[0], 3), 255, dtype=np.uint8),
                ])
                first = Image.fromarray(first, 'RGB')
            pages.append(first)
            first = img

    pages.append(first)
    return pages


def convert_to_rgb(img):
    # default size = A4
    if len(img.split()) == 3:
        return img
    rgb = Image.new('RGB', img.size, (255, 255, 255))
    rgb.paste(img, mask=img.split()[-1])
    return rgb


def convert_to_pdf(images, pdf_file_path, ms=False):
    """images: list of str, which has image paths"""
    image_files = []
    for filename in images:
        image_files.append(convert_to_rgb(Image.open(filename)))
    if ms:
        size = (2339, 1653)
    else:
        size = (1653, 2339)
    pages = merge_pages(image_files, size=size)

    pages[0].save(pdf_file_path,
                  'PDF',
                  resolution=100.0,
                  save_all=True,
                  append_images=pages[1:])


def upload_pdf(pdf_file_path, bucket):
    blob = bucket.blob(pdf_file_path)
    blob.upload_from_filename(pdf_file_path)
