"""
Evaluate person detection against ground truth annotations.
Calculates Precision, Recall, F1 Score, and IoU metrics.
"""

import cv2
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BBoxMetrics:
    """Calculate bounding box evaluation metrics."""
    
    @staticmethod
    def calculate_iou(bbox1: List[float], bbox2: List[float]) -> float:
        """
        Calculate Intersection over Union (IoU) between two bounding boxes.
        
        Args:
            bbox1: [x1, y1, x2, y2]
            bbox2: [x1, y1, x2, y2]
            
        Returns:
            IoU value between 0 and 1
        """
        x1_min, y1_min, x1_max, y1_max = bbox1
        x2_min, y2_min, x2_max, y2_max = bbox2
        
        # Calculate intersection
        inter_xmin = max(x1_min, x2_min)
        inter_ymin = max(y1_min, y2_min)
        inter_xmax = min(x1_max, x2_max)
        inter_ymax = min(y1_max, y2_max)
        
        if inter_xmax < inter_xmin or inter_ymax < inter_ymin:
            return 0.0
        
        inter_area = (inter_xmax - inter_xmin) * (inter_ymax - inter_ymin)
        
        # Calculate union
        bbox1_area = (x1_max - x1_min) * (y1_max - y1_min)
        bbox2_area = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = bbox1_area + bbox2_area - inter_area
        
        if union_area == 0:
            return 0.0
        
        return inter_area / union_area
    
    @staticmethod
    def match_detections(detections: List[Dict], ground_truths: List[Dict], 
                        iou_threshold: float = 0.5) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Match detections with ground truth using IoU.
        
        Args:
            detections: List of detected bboxes with format
                       [{'bbox': [x1,y1,x2,y2], 'confidence': float}, ...]
            ground_truths: List of ground truth bboxes
                          [{'bbox': [x1,y1,x2,y2], 'person_id': str}, ...]
            iou_threshold: Minimum IoU for match (default 0.5)
            
        Returns:
            Tuple of (true_positives, false_positives, false_negatives)
        """
        true_positives = []
        false_positives = []
        false_negatives = []
        matched_gts = set()
        
        # Match detections to ground truths
        for det in detections:
            best_iou = 0
            best_gt_idx = -1
            
            for gt_idx, gt in enumerate(ground_truths):
                if gt_idx in matched_gts:
                    continue
                
                iou = BBoxMetrics.calculate_iou(det['bbox'], gt['bbox'])
                if iou > best_iou:
                    best_iou = iou
                    best_gt_idx = gt_idx
            
            if best_iou >= iou_threshold and best_gt_idx >= 0:
                true_positives.append({
                    'detection': det,
                    'ground_truth': ground_truths[best_gt_idx],
                    'iou': best_iou
                })
                matched_gts.add(best_gt_idx)
            else:
                false_positives.append({
                    'detection': det,
                    'best_iou': best_iou
                })
        
        # Remaining ground truths are false negatives
        for gt_idx, gt in enumerate(ground_truths):
            if gt_idx not in matched_gts:
                false_negatives.append(gt)
        
        return true_positives, false_positives, false_negatives


class PersonDetectionEvaluator:
    """Evaluate person detection against ground truth."""
    
    def __init__(self, detector_class, ground_truth_parser_class, 
                 video_dir: str, annotations_file: str, 
                 iou_threshold: float = 0.5,
                 confidence_threshold: float = 0.5):
        """
        Initialize evaluator.
        
        Args:
            detector_class: PersonDetector class from detector.py
            ground_truth_parser_class: GroundTruthParser class
            video_dir: Directory containing video files
            annotations_file: Path to ground truth Excel file
            iou_threshold: Minimum IoU for positive match
            confidence_threshold: Minimum detection confidence
        """
        self.detector = detector_class(confidence=confidence_threshold)
        self.parser = ground_truth_parser_class(annotations_file)
        self.video_dir = Path(video_dir)
        self.iou_threshold = iou_threshold
        self.confidence_threshold = confidence_threshold
        self.results = {}
        self.frame_results = []
        
        # Load ground truth
        self.parser.load_annotations()
        self.ground_truth = self.parser.parse_ground_truth()
    
    def get_video_fps(self, video_path: str) -> float:
        """Get video frames per second."""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        return fps
    
    def process_video(self, video_name: str, max_frames: Optional[int] = None) -> Dict:
        """
        Process single video and compare detections with ground truth.
        
        Args:
            video_name: Name of video file (e.g., 'video1.mp4')
            max_frames: Maximum frames to process (None = all)
            
        Returns:
            Evaluation results for the video
        """
        video_path = self.video_dir / video_name
        
        if not video_path.exists():
            logger.warning(f"⚠️  Video not found: {video_path}")
            return None
        
        logger.info(f"\n🎥 Processing: {video_name}")
        
        # Get ground truth for this video
        video_gt = self.ground_truth.get(video_name)
        if not video_gt:
            logger.warning(f"   No ground truth annotations for {video_name}")
            return None
        
        # Open video
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(f"   FPS: {fps}, Total frames: {frame_count}")
        
        video_results = {
            'video_name': video_name,
            'fps': fps,
            'total_frames': frame_count,
            'frame_results': [],
            'metrics': {
                'total_tp': 0,
                'total_fp': 0,
                'total_fn': 0,
                'total_detections': 0,
                'total_annotations': video_gt['total_annotations']
            }
        }
        
        frame_idx = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if max_frames and frame_idx >= max_frames:
                break
            
            # Calculate frame timestamp in milliseconds
            frame_ms = int(frame_idx / fps * 1000) if fps > 0 else 0
            
            # Get ground truth for this frame (with tolerance)
            frame_gts = self.parser.get_frame_annotations(video_name, frame_ms, tolerance_ms=50)
            
            if not frame_gts:
                frame_idx += 1
                continue
            
            # Run detection
            detections = self.detector.detect_people(frame)
            
            # Convert detections to format expected by metrics
            det_dicts = [{'bbox': d, 'confidence': self.confidence_threshold} for d in detections]
            
            # Match with ground truth
            tp, fp, fn = BBoxMetrics.match_detections(det_dicts, frame_gts, self.iou_threshold)
            
            # Record frame results
            frame_result = {
                'video_name': video_name,
                'frame_idx': frame_idx,
                'frame_ms': frame_ms,
                'num_detections': len(detections),
                'num_ground_truths': len(frame_gts),
                'tp': len(tp),
                'fp': len(fp),
                'fn': len(fn),
                'mean_iou': np.mean([m['iou'] for m in tp]) if tp else 0.0
            }
            
            video_results['frame_results'].append(frame_result)
            
            # Update aggregate metrics
            video_results['metrics']['total_tp'] += len(tp)
            video_results['metrics']['total_fp'] += len(fp)
            video_results['metrics']['total_fn'] += len(fn)
            video_results['metrics']['total_detections'] += len(detections)
            
            self.frame_results.append(frame_result)
            
            if frame_idx % 30 == 0:
                logger.info(f"   Processed frame {frame_idx}/{frame_count}")
            
            frame_idx += 1
        
        cap.release()
        
        # Calculate metrics
        tp = video_results['metrics']['total_tp']
        fp = video_results['metrics']['total_fp']
        fn = video_results['metrics']['total_fn']
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        video_results['metrics']['precision'] = precision
        video_results['metrics']['recall'] = recall
        video_results['metrics']['f1_score'] = f1
        
        logger.info(f"\n   ✅ Results for {video_name}:")
        logger.info(f"      Precision: {precision:.3f}")
        logger.info(f"      Recall: {recall:.3f}")
        logger.info(f"      F1 Score: {f1:.3f}")
        logger.info(f"      TP: {tp}, FP: {fp}, FN: {fn}")
        
        self.results[video_name] = video_results
        return video_results
    
    def evaluate_all_videos(self, max_frames_per_video: Optional[int] = None) -> Dict:
        """
        Evaluate all videos with ground truth annotations.
        
        Args:
            max_frames_per_video: Max frames per video (None = all)
            
        Returns:
            Dictionary with results for all videos
        """
        logger.info(f"🔄 Starting evaluation for {len(self.ground_truth)} videos...")
        
        for video_name in self.ground_truth.keys():
            self.process_video(video_name, max_frames_per_video)
        
        return self.results
    
    def get_summary_metrics(self) -> Dict:
        """Get aggregate metrics across all videos."""
        if not self.results:
            return {}
        
        total_tp = sum(r['metrics']['total_tp'] for r in self.results.values())
        total_fp = sum(r['metrics']['total_fp'] for r in self.results.values())
        total_fn = sum(r['metrics']['total_fn'] for r in self.results.values())
        
        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        summary = {
            'total_videos': len(self.results),
            'total_frames_evaluated': len(self.frame_results),
            'total_tp': total_tp,
            'total_fp': total_fp,
            'total_fn': total_fn,
            'overall_precision': precision,
            'overall_recall': recall,
            'overall_f1_score': f1,
            'evaluation_timestamp': datetime.now().isoformat()
        }
        
        return summary
    
    def get_results_dataframe(self) -> pd.DataFrame:
        """Convert frame results to pandas DataFrame."""
        return pd.DataFrame(self.frame_results)


if __name__ == '__main__':
    # Example usage
    from detector import PersonDetector
    from parse_ground_truth import GroundTruthParser
    
    # Initialize evaluator
    evaluator = PersonDetectionEvaluator(
        detector_class=PersonDetector,
        ground_truth_parser_class=GroundTruthParser,
        video_dir='sample_video/videos/',
        annotations_file='sample_annotations.xlsx',
        iou_threshold=0.5,
        confidence_threshold=0.5
    )
    
    # Evaluate all videos
    results = evaluator.evaluate_all_videos(max_frames_per_video=100)
    
    # Get summary
    summary = evaluator.get_summary_metrics()
    print("\n📊 Summary Metrics:")
    print(summary)
    
    # Get detailed results
    df_results = evaluator.get_results_dataframe()
    print("\n📋 Detailed Results:")
    print(df_results.head(20))
