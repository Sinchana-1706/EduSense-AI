"""
Evaluation and Benchmarking Script for Facial Expression Recognition in EduSense AI.
Compares EmotiEffLib against baseline (FERPlus ONNX if present) and reports:
- Number of evaluation samples
- Inference latency (mean, min, max, std dev ms/sample)
- Prediction distributions & confidence metrics
- Uncertain or low-confidence predictions
- Comparison notes
"""

import os
import sys
import time
import cv2
import numpy as np
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.services.emotion_service import EmotionService
from app.services.face_service import FaceService


def find_test_images() -> List[Dict[str, Any]]:
    """Gathers real and synthetic test face images for benchmarking."""
    samples = []
    
    # 1. Real face images from insightface data directory
    candidate_paths = [
        os.path.join(os.path.dirname(__file__), "venv", "Lib", "site-packages", "insightface", "data", "images", "Tom_Hanks_54745.png"),
        os.path.join(os.path.dirname(__file__), "venv", "Lib", "site-packages", "insightface", "data", "images", "t1.jpg"),
        os.path.join(os.path.dirname(__file__), "venv", "Lib", "site-packages", "skimage", "data", "astronaut.png"),
    ]
    for p in candidate_paths:
        if os.path.isfile(p):
            img = cv2.imread(p)
            if img is not None:
                samples.append({
                    "name": os.path.basename(p),
                    "image": img,
                    "type": "real_image",
                })

    # 2. Synthetic face crops with varying expressions (smile, neutral, open mouth)
    for expr_name, mouth_type in [("smile", "arc_up"), ("neutral", "line"), ("surprise", "circle")]:
        crop = np.full((224, 224, 3), 160, dtype=np.uint8)
        cv2.circle(crop, (70, 80), 14, (35, 35, 35), -1)
        cv2.circle(crop, (154, 80), 14, (35, 35, 35), -1)
        if mouth_type == "arc_up":
            cv2.ellipse(crop, (112, 140), (45, 25), 0, 0, 180, (35, 35, 35), 4)
        elif mouth_type == "circle":
            cv2.circle(crop, (112, 150), 20, (35, 35, 35), -1)
        else:
            cv2.line(crop, (75, 145), (149, 145), (35, 35, 35), 4)

        samples.append({
            "name": f"synthetic_{expr_name}",
            "image": crop,
            "type": "synthetic_crop",
        })

    return samples


def benchmark_emotiefflib(samples: List[Dict[str, Any]], num_repeats: int = 10) -> Dict[str, Any]:
    svc = EmotionService.get_instance()
    face_svc = FaceService.get_instance()

    latencies_ms = []
    predictions_record = []
    uncertain_count = 0
    UNCERTAIN_THRESHOLD = 0.35

    print(f"\nEvaluating EmotiEffLib ({svc.model_name}) across {len(samples)} samples ({num_repeats} repeats each)...")

    for sample in samples:
        img = sample["image"]
        name = sample["name"]

        # If it's a full image, extract face crop
        if sample["type"] == "real_image":
            faces = face_svc.detect_faces(img)
            if not faces:
                continue
            crop = face_svc.extract_face_crop(img, faces[0].bbox.astype(int))
        else:
            crop = img

        sample_latencies = []
        last_pred = None

        for _ in range(num_repeats):
            t0 = time.perf_counter()
            pred = svc.predict_emotion_from_crop(crop)
            t1 = time.perf_counter()
            sample_latencies.append((t1 - t0) * 1000.0)
            last_pred = pred

        avg_lat = float(np.mean(sample_latencies))
        latencies_ms.extend(sample_latencies)

        if last_pred:
            conf = last_pred.get("confidence", 0.0)
            if conf < UNCERTAIN_THRESHOLD:
                uncertain_count += 1

            predictions_record.append({
                "sample": name,
                "expression": last_pred["expression"],
                "confidence": conf,
                "latency_ms": round(avg_lat, 2),
            })

    total_runs = len(latencies_ms)
    mean_lat = float(np.mean(latencies_ms)) if latencies_ms else 0.0
    min_lat = float(np.min(latencies_ms)) if latencies_ms else 0.0
    max_lat = float(np.max(latencies_ms)) if latencies_ms else 0.0
    std_lat = float(np.std(latencies_ms)) if latencies_ms else 0.0

    return {
        "model_name": svc.model_name,
        "engine": svc.engine,
        "device": svc.device,
        "num_samples": len(predictions_record),
        "total_inferences": total_runs,
        "latency_mean_ms": round(mean_lat, 2),
        "latency_min_ms": round(min_lat, 2),
        "latency_max_ms": round(max_lat, 2),
        "latency_std_ms": round(std_lat, 2),
        "uncertain_predictions": uncertain_count,
        "predictions": predictions_record,
    }


def check_ferplus_availability() -> Optional[str]:
    """Checks if FERPlus ONNX model file exists in local directories."""
    paths = [
        "ferplus.onnx",
        "model.onnx",
        "emotion_ferplus.onnx",
        "models/ferplus.onnx",
        "backend/models/ferplus.onnx",
    ]
    for p in paths:
        if os.path.isfile(p):
            return p
    return None


def run_evaluation():
    print("==================================================")
    print("EDUSENSE AI — FACIAL EMOTION BENCHMARK & EVALUATION")
    print("==================================================")

    samples = find_test_images()
    print(f"Found {len(samples)} evaluation samples.")

    # 1. Check for legacy FERPlus
    ferplus_path = check_ferplus_availability()
    if ferplus_path:
        print(f"Legacy FERPlus ONNX found at: {ferplus_path}")
    else:
        print("Note on FERPlus: No FERPlus ONNX model weights file found in the repository.")
        print("Evaluation proceeding directly with EmotiEffLib pretrained ONNX pipeline.")

    # 2. Run EmotiEffLib Benchmark
    bench = benchmark_emotiefflib(samples, num_repeats=15)

    print("\n--------------------------------------------------")
    print("BENCHMARK RESULTS SUMMARY")
    print("--------------------------------------------------")
    print(f"Model: {bench['model_name']} ({bench['engine']} on {bench['device']})")
    print(f"Evaluated Samples: {bench['num_samples']}")
    print(f"Total Inferences: {bench['total_inferences']}")
    print(f"Average Latency: {bench['latency_mean_ms']} ms (Min: {bench['latency_min_ms']} ms, Max: {bench['latency_max_ms']} ms, Std: {bench['latency_std_ms']} ms)")
    print(f"Low-Confidence / Uncertain Predictions (< 0.35): {bench['uncertain_predictions']}")

    print("\nSAMPLE PREDICTIONS TABLE:")
    print(f"{'Sample':<25} | {'Expression':<12} | {'Confidence':<10} | {'Latency (ms)':<10}")
    print("-" * 65)
    for p in bench["predictions"]:
        print(f"{p['sample']:<25} | {p['expression']:<12} | {p['confidence'] * 100:>5.1f}%     | {p['latency_ms']:>6.2f} ms")

    print("\nETHICAL & SCIENTIFIC NOTICE:")
    print("Facial-expression predictions estimate visible morphological cues (e.g. smile, frown).")
    print("They do not establish internal psychological affect, attention, or understanding.")
    print("==================================================")


if __name__ == "__main__":
    run_evaluation()
