import os
import cv2
import argparse
import supervision as sv
from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(description="YOLO检测并保存结果图")
    parser.add_argument("-m", "--model", required=True, help="YOLO 模型路径（*.pt）")
    parser.add_argument("-i", "--input", required=True, help="输入图片路径")
    parser.add_argument("-o", "--output", required=True, help="输出图片保存路径")
    return parser.parse_args()


def main():
    args = parse_args()

    image = cv2.imread(args.input)
    if image is None:
        raise FileNotFoundError(f"无法读取图片：{args.input}")

    if not os.path.isfile(args.model):
        raise FileNotFoundError(f"模型文件不存在：{args.model}")
    model = YOLO(args.model)

    result = model(image)[0]
    detections = sv.Detections.from_ultralytics(result)

    box_annotator = sv.BoxAnnotator()
    annotated = box_annotator.annotate(scene=image, detections=detections)

    cv2.imwrite(args.output, annotated)
    print(f"结果已保存至：{args.output}")


if __name__ == "__main__":
    main()
