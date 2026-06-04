"""
Main evaluation pipeline orchestration.
Combines parsing, evaluation, and reporting into a single workflow.

Usage:
    python evaluate_pipeline.py --annotations annotations.xlsx --videos video_dir --output results_dir
"""

import argparse
import sys
from pathlib import Path
import logging

from parse_ground_truth import GroundTruthParser, create_sample_annotation_file
from evaluate_with_ground_truth import PersonDetectionEvaluator
from export_results import EvaluationReporter
from detector import PersonDetector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Person Detection Evaluation Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python evaluate_pipeline.py \\
    --annotations ground_truth.xlsx \\
    --videos sample_video/videos \\
    --output evaluation_results
  
  # With custom settings
  python evaluate_pipeline.py \\
    --annotations ground_truth.xlsx \\
    --videos sample_video/videos \\
    --output evaluation_results \\
    --iou-threshold 0.5 \\
    --confidence 0.5 \\
    --max-frames 500
  
  # Generate sample files
  python evaluate_pipeline.py --generate-sample
        """
    )
    
    parser.add_argument(
        '--annotations',
        type=str,
        default='ground_truth.xlsx',
        help='Path to ground truth annotations Excel file'
    )
    
    parser.add_argument(
        '--videos',
        type=str,
        default='sample_video/videos',
        help='Directory containing video files'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='evaluation_results',
        help='Output directory for results'
    )
    
    parser.add_argument(
        '--iou-threshold',
        type=float,
        default=0.5,
        help='Minimum IoU for detection matching (default: 0.5)'
    )
    
    parser.add_argument(
        '--confidence',
        type=float,
        default=0.5,
        help='Detection confidence threshold (default: 0.5)'
    )
    
    parser.add_argument(
        '--max-frames',
        type=int,
        default=None,
        help='Maximum frames per video to process (default: all)'
    )
    
    parser.add_argument(
        '--generate-sample',
        action='store_true',
        help='Generate sample annotation file and exit'
    )
    
    args = parser.parse_args()
    
    # Generate sample if requested
    if args.generate_sample:
        create_sample_annotation_file('sample_annotations.xlsx')
        logger.info("✅ Sample annotation file created: sample_annotations.xlsx")
        return 0
    
    # Validate inputs
    annotations_path = Path(args.annotations)
    videos_path = Path(args.videos)
    
    if not annotations_path.exists():
        logger.error(f"❌ Annotations file not found: {annotations_path}")
        return 1
    
    if not videos_path.exists():
        logger.error(f"❌ Videos directory not found: {videos_path}")
        return 1
    
    try:
        logger.info("🚀 Starting Person Detection Evaluation Pipeline")
        logger.info(f"   Annotations: {annotations_path}")
        logger.info(f"   Videos: {videos_path}")
        logger.info(f"   Output: {args.output}")
        logger.info(f"   IoU Threshold: {args.iou_threshold}")
        logger.info(f"   Confidence: {args.confidence}")
        if args.max_frames:
            logger.info(f"   Max Frames: {args.max_frames}")
        
        # Step 1: Parse ground truth
        logger.info("\n📋 Step 1: Parsing Ground Truth...")
        parser = GroundTruthParser(str(annotations_path))
        parser.load_annotations()
        ground_truth = parser.parse_ground_truth()
        
        # Step 2: Run evaluation
        logger.info("\n🎥 Step 2: Running Evaluation...")
        evaluator = PersonDetectionEvaluator(
            detector_class=PersonDetector,
            ground_truth_parser_class=GroundTruthParser,
            video_dir=str(videos_path),
            annotations_file=str(annotations_path),
            iou_threshold=args.iou_threshold,
            confidence_threshold=args.confidence
        )
        
        results = evaluator.evaluate_all_videos(max_frames_per_video=args.max_frames)
        summary = evaluator.get_summary_metrics()
        frame_results_df = evaluator.get_results_dataframe()
        
        # Step 3: Generate reports
        logger.info("\n📊 Step 3: Generating Reports...")
        reporter = EvaluationReporter(output_dir=args.output)
        reporter.generate_complete_report(summary, results, frame_results_df)
        
        # Print final summary
        logger.info("\n" + "="*60)
        logger.info("📊 FINAL EVALUATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Total Videos: {summary['total_videos']}")
        logger.info(f"Total Frames Evaluated: {summary['total_frames_evaluated']}")
        logger.info(f"Overall Precision: {summary['overall_precision']:.4f}")
        logger.info(f"Overall Recall: {summary['overall_recall']:.4f}")
        logger.info(f"Overall F1 Score: {summary['overall_f1_score']:.4f}")
        logger.info(f"True Positives: {summary['total_tp']}")
        logger.info(f"False Positives: {summary['total_fp']}")
        logger.info(f"False Negatives: {summary['total_fn']}")
        logger.info("="*60)
        
        logger.info(f"\n✅ Pipeline completed successfully!")
        logger.info(f"📁 Results saved to: {args.output}")
        
        return 0
        
    except Exception as e:
        logger.error(f"\n❌ Error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
