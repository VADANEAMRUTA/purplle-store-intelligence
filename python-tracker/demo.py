"""
Demonstration script showing how to use the evaluation pipeline.
Run this to see the complete workflow in action.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from parse_ground_truth import GroundTruthParser, create_sample_annotation_file
from evaluate_with_ground_truth import PersonDetectionEvaluator, BBoxMetrics
from export_results import EvaluationReporter
from evaluation_utils import batch_validate_videos, batch_validate_annotations
from detector import PersonDetector
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_1_parse_ground_truth():
    """Demo 1: Parse ground truth annotations."""
    logger.info("\n" + "="*60)
    logger.info("DEMO 1: Parsing Ground Truth Annotations")
    logger.info("="*60)
    
    # Create sample annotation file
    sample_file = 'demo_annotations.xlsx'
    create_sample_annotation_file(sample_file)
    
    # Parse annotations
    parser = GroundTruthParser(sample_file)
    parser.load_annotations()
    ground_truth = parser.parse_ground_truth()
    
    # Display parsed data
    for video_name, data in ground_truth.items():
        logger.info(f"\nVideo: {video_name}")
        logger.info(f"  Total annotations: {data['total_annotations']}")
        logger.info(f"  Event types: {data['event_types']}")
        logger.info(f"  Frames with annotations: {len(data['frames'])}")
        
        # Show first annotation
        first_frame = list(data['frames'].values())[0][0]
        logger.info(f"  First annotation:")
        logger.info(f"    - Event: {first_frame['event_type']}")
        logger.info(f"    - Person: {first_frame['person_id']}")
        logger.info(f"    - BBox: {first_frame['bbox']}")
        logger.info(f"    - Area: {first_frame['area']:.2f} px²")
    
    # Export to CSV
    csv_file = 'demo_parsed_annotations.csv'
    parser.export_to_csv(csv_file)
    logger.info(f"\n✅ Exported to: {csv_file}")
    
    return parser


def demo_2_bbox_metrics():
    """Demo 2: Bounding box calculations."""
    logger.info("\n" + "="*60)
    logger.info("DEMO 2: Bounding Box Metrics")
    logger.info("="*60)
    
    # Example bounding boxes
    bbox_gt = [100, 50, 200, 300]  # Ground truth
    bbox_det_perfect = [100, 50, 200, 300]  # Perfect detection
    bbox_det_partial = [110, 60, 210, 290]  # Partial overlap
    bbox_det_miss = [300, 300, 400, 400]  # Complete miss
    
    logger.info(f"\nGround Truth: {bbox_gt}")
    
    # Calculate IoUs
    iou_perfect = BBoxMetrics.calculate_iou(bbox_gt, bbox_det_perfect)
    iou_partial = BBoxMetrics.calculate_iou(bbox_gt, bbox_det_partial)
    iou_miss = BBoxMetrics.calculate_iou(bbox_gt, bbox_det_miss)
    
    logger.info(f"\nDetections:")
    logger.info(f"  Perfect match {bbox_det_perfect}: IoU = {iou_perfect:.4f}")
    logger.info(f"  Partial match {bbox_det_partial}: IoU = {iou_partial:.4f}")
    logger.info(f"  Complete miss {bbox_det_miss}: IoU = {iou_miss:.4f}")
    
    # Match detections
    detections = [
        {'bbox': bbox_det_perfect, 'confidence': 0.9},
        {'bbox': bbox_det_partial, 'confidence': 0.8},
    ]
    ground_truths = [
        {'bbox': bbox_gt, 'person_id': 'person_1'},
    ]
    
    tp, fp, fn = BBoxMetrics.match_detections(detections, ground_truths, iou_threshold=0.5)
    
    logger.info(f"\nMatching (threshold=0.5):")
    logger.info(f"  True Positives: {len(tp)}")
    logger.info(f"  False Positives: {len(fp)}")
    logger.info(f"  False Negatives: {len(fn)}")
    
    if tp:
        for t in tp:
            logger.info(f"    TP: IoU = {t['iou']:.4f}")


def demo_3_validation():
    """Demo 3: Batch validation."""
    logger.info("\n" + "="*60)
    logger.info("DEMO 3: Validation Utilities")
    logger.info("="*60)
    
    # Validate annotation file
    annotation_file = 'demo_annotations.xlsx'
    video_dir = 'sample_video/videos'
    
    logger.info(f"\nValidating annotations: {annotation_file}")
    from evaluation_utils import ExcelUtilities
    is_valid, errors = ExcelUtilities.validate_annotation_file(annotation_file)
    
    if is_valid:
        logger.info("  ✅ Annotation file is valid")
    else:
        logger.warning("  ⚠️  Validation errors:")
        for error in errors:
            logger.warning(f"    - {error}")
    
    # Validate videos if directory exists
    if Path(video_dir).exists():
        logger.info(f"\nValidating videos in: {video_dir}")
        video_validation = batch_validate_videos(video_dir)
        valid_count = sum(1 for v in video_validation.values() if v['status'] == 'valid')
        logger.info(f"  {valid_count}/{len(video_validation)} videos valid")
    else:
        logger.info(f"\n⚠️  Video directory not found: {video_dir}")


def demo_4_metrics_calculation():
    """Demo 4: Metrics calculation."""
    logger.info("\n" + "="*60)
    logger.info("DEMO 4: Metrics Calculation")
    logger.info("="*60)
    
    # Example results
    tp, fp, fn = 80, 15, 10
    
    logger.info(f"\nDetection Results:")
    logger.info(f"  True Positives (TP): {tp}")
    logger.info(f"  False Positives (FP): {fp}")
    logger.info(f"  False Negatives (FN): {fn}")
    
    # Calculate metrics
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    logger.info(f"\nCalculated Metrics:")
    logger.info(f"  Precision: {precision:.4f} ({precision*100:.2f}%)")
    logger.info(f"    → Of {tp + fp} detections, {tp} were correct")
    logger.info(f"  Recall: {recall:.4f} ({recall*100:.2f}%)")
    logger.info(f"    → Of {tp + fn} ground truths, {tp} were detected")
    logger.info(f"  F1 Score: {f1:.4f}")
    logger.info(f"    → Harmonic mean of Precision and Recall")
    
    # Quality assessment
    logger.info(f"\nQuality Assessment:")
    if f1 >= 0.8:
        logger.info("  ⭐⭐⭐ Excellent performance")
    elif f1 >= 0.7:
        logger.info("  ⭐⭐ Good performance")
    elif f1 >= 0.5:
        logger.info("  ⭐ Fair performance (needs improvement)")
    else:
        logger.info("  ❌ Poor performance (significant issues)")


def demo_5_report_generation():
    """Demo 5: Report generation example."""
    logger.info("\n" + "="*60)
    logger.info("DEMO 5: Report Generation")
    logger.info("="*60)
    
    # Example metrics
    summary_metrics = {
        'total_videos': 3,
        'total_frames_evaluated': 1250,
        'overall_precision': 0.8234,
        'overall_recall': 0.7654,
        'overall_f1_score': 0.7934,
        'total_tp': 245,
        'total_fp': 52,
        'total_fn': 65
    }
    
    logger.info(f"\nSample Summary Metrics:")
    for key, value in summary_metrics.items():
        if isinstance(value, float):
            logger.info(f"  {key}: {value:.4f}")
        else:
            logger.info(f"  {key}: {value}")
    
    logger.info(f"\nTo generate actual reports, run:")
    logger.info(f"  python evaluate_pipeline.py --generate-sample")
    logger.info(f"  python evaluate_pipeline.py \\")
    logger.info(f"    --annotations demo_annotations.xlsx \\")
    logger.info(f"    --videos sample_video/videos \\")
    logger.info(f"    --output demo_results")


def demo_6_end_to_end():
    """Demo 6: End-to-end workflow."""
    logger.info("\n" + "="*60)
    logger.info("DEMO 6: Complete End-to-End Workflow")
    logger.info("="*60)
    
    logger.info(f"\nComplete workflow steps:")
    logger.info(f"  1. Parse ground truth annotations")
    logger.info(f"  2. Run person detector on videos")
    logger.info(f"  3. Match detections with ground truth using IoU")
    logger.info(f"  4. Calculate Precision, Recall, F1")
    logger.info(f"  5. Generate visualizations and reports")
    logger.info(f"  6. Export results to Excel, PDF, JSON")
    
    logger.info(f"\nTo run the complete pipeline:")
    logger.info(f"  python evaluate_pipeline.py \\")
    logger.info(f"    --annotations ground_truth.xlsx \\")
    logger.info(f"    --videos videos/ \\")
    logger.info(f"    --output evaluation_results \\")
    logger.info(f"    --iou-threshold 0.5 \\")
    logger.info(f"    --confidence 0.5")
    
    logger.info(f"\nFor more information:")
    logger.info(f"  - Read: SETUP_GUIDE.md")
    logger.info(f"  - Read: QUICK_REFERENCE.md")
    logger.info(f"  - Read: EVALUATION_README.md")


def main():
    """Run all demonstrations."""
    logger.info("\n" + "🎓 "*30)
    logger.info("PERSON DETECTION EVALUATION PIPELINE - DEMONSTRATIONS")
    logger.info("🎓 "*30)
    
    try:
        # Run demonstrations
        demo_1_parse_ground_truth()
        demo_2_bbox_metrics()
        demo_3_validation()
        demo_4_metrics_calculation()
        demo_5_report_generation()
        demo_6_end_to_end()
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("DEMONSTRATION COMPLETE")
        logger.info("="*60)
        logger.info("\nGenerated demo files:")
        logger.info("  - demo_annotations.xlsx")
        logger.info("  - demo_parsed_annotations.csv")
        
        logger.info("\n✅ All demonstrations completed successfully!")
        logger.info("\nNext steps:")
        logger.info("  1. Review generated files")
        logger.info("  2. Prepare your ground truth Excel file")
        logger.info("  3. Run: python evaluate_pipeline.py --generate-sample")
        logger.info("  4. Run: python evaluate_pipeline.py [your options]")
        
        return 0
        
    except Exception as e:
        logger.error(f"\n❌ Error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
