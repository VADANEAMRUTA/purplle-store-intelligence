"""
Helper utilities for the evaluation pipeline.
Provides utility functions for common tasks.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import cv2
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class VideoUtilities:
    """Video processing utilities."""
    
    @staticmethod
    def get_video_info(video_path: str) -> dict:
        """
        Get metadata about a video file.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video info
        """
        cap = cv2.VideoCapture(video_path)
        
        info = {
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'codec': int(cap.get(cv2.CAP_PROP_FOURCC))
        }
        
        cap.release()
        
        # Calculate duration
        if info['fps'] > 0:
            info['duration_seconds'] = info['total_frames'] / info['fps']
        else:
            info['duration_seconds'] = 0
        
        return info
    
    @staticmethod
    def list_videos(video_dir: str) -> List[str]:
        """List all video files in directory."""
        video_dir = Path(video_dir)
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}
        
        videos = []
        for file in sorted(video_dir.iterdir()):
            if file.suffix.lower() in video_extensions:
                videos.append(file.name)
        
        return videos
    
    @staticmethod
    def get_frame_at_time(video_path: str, timestamp_ms: int) -> Tuple[bool, np.ndarray]:
        """
        Get frame at specific timestamp.
        
        Args:
            video_path: Path to video file
            timestamp_ms: Timestamp in milliseconds
            
        Returns:
            Tuple of (success, frame)
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        if fps <= 0:
            return False, None
        
        frame_idx = int(timestamp_ms / 1000.0 * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        cap.release()
        
        return ret, frame


class ExcelUtilities:
    """Excel file utilities."""
    
    @staticmethod
    def validate_annotation_file(excel_file: str) -> Tuple[bool, List[str]]:
        """
        Validate annotation Excel file format.
        
        Args:
            excel_file: Path to Excel file
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        try:
            df = pd.read_excel(excel_file)
        except Exception as e:
            return False, [f"Cannot read Excel file: {e}"]
        
        # Check required columns
        required_cols = {'video_name', 'timestamp', 'event_type', 'person_id', 'bbox'}
        actual_cols = set(df.columns)
        
        missing_cols = required_cols - actual_cols
        if missing_cols:
            errors.append(f"Missing columns: {missing_cols}")
        
        # Check for empty rows
        if df.isnull().any().any():
            errors.append(f"Found {df.isnull().sum().sum()} null values")
        
        # Validate timestamp format
        if 'timestamp' in df.columns:
            for idx, ts in enumerate(df['timestamp']):
                ts_str = str(ts).strip()
                if not _is_valid_timestamp(ts_str):
                    errors.append(f"Invalid timestamp at row {idx + 2}: '{ts_str}'")
                    break
        
        # Validate bbox format
        if 'bbox' in df.columns:
            for idx, bbox in enumerate(df['bbox']):
                bbox_str = str(bbox).strip('[]')
                try:
                    coords = [float(x.strip()) for x in bbox_str.split(',')]
                    if len(coords) != 4:
                        errors.append(f"Invalid bbox format at row {idx + 2}: {bbox}")
                except:
                    errors.append(f"Cannot parse bbox at row {idx + 2}: {bbox}")
                    break
        
        return len(errors) == 0, errors
    
    @staticmethod
    def create_empty_template(output_file: str):
        """Create empty annotation template."""
        template_data = {
            'video_name': ['video1.mp4'],
            'timestamp': ['00:00:05'],
            'event_type': ['ENTRY'],
            'person_id': ['person_1'],
            'bbox': ['[100,50,200,300]']
        }
        
        df = pd.DataFrame(template_data)
        df.to_excel(output_file, index=False)
        logger.info(f"✅ Created template: {output_file}")


class ResultsUtilities:
    """Results analysis utilities."""
    
    @staticmethod
    def load_evaluation_results(results_dir: str) -> dict:
        """Load all evaluation results from output directory."""
        results_dir = Path(results_dir)
        
        results = {}
        
        # Load summary
        summary_file = results_dir / 'evaluation_summary.xlsx'
        if summary_file.exists():
            summary_df = pd.read_excel(summary_file, sheet_name='Summary', header=None)
            results['summary'] = summary_df
        
        # Load detailed results
        detailed_file = results_dir / 'evaluation_detailed.xlsx'
        if detailed_file.exists():
            results['frame_results'] = pd.read_excel(detailed_file, sheet_name='Frame Results')
            results['video_summary'] = pd.read_excel(detailed_file, sheet_name='Video Summary')
        
        return results
    
    @staticmethod
    def compare_evaluations(results1: dict, results2: dict) -> pd.DataFrame:
        """
        Compare two evaluation results.
        
        Args:
            results1: First evaluation results
            results2: Second evaluation results
            
        Returns:
            DataFrame with comparison
        """
        comparison_data = []
        
        for key in ['overall_precision', 'overall_recall', 'overall_f1_score']:
            val1 = results1.get(key, 0)
            val2 = results2.get(key, 0)
            diff = val2 - val1
            pct_change = (diff / val1 * 100) if val1 != 0 else 0
            
            comparison_data.append({
                'metric': key,
                'value_1': val1,
                'value_2': val2,
                'difference': diff,
                'percent_change': pct_change
            })
        
        return pd.DataFrame(comparison_data)
    
    @staticmethod
    def export_for_submission(results_dir: str, output_file: str):
        """
        Create submission-ready Excel file with key results.
        
        Args:
            results_dir: Results directory
            output_file: Output Excel file
        """
        results = ResultsUtilities.load_evaluation_results(results_dir)
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Summary metrics
            if 'summary' in results:
                results['summary'].to_excel(writer, sheet_name='Summary', index=False, header=False)
            
            # Video summary
            if 'video_summary' in results:
                results['video_summary'].to_excel(writer, sheet_name='Video Results', index=False)
            
            # Frame results
            if 'frame_results' in results:
                results['frame_results'].to_excel(writer, sheet_name='Frame Details', index=False)
        
        logger.info(f"✅ Created submission file: {output_file}")


def _is_valid_timestamp(timestamp_str: str) -> bool:
    """Check if timestamp is valid HH:MM:SS format."""
    try:
        parts = timestamp_str.split(':')
        if len(parts) != 3:
            return False
        
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        
        return 0 <= hours < 24 and 0 <= minutes < 60 and 0 <= seconds < 60
    except:
        return False


# Batch operations

def batch_validate_videos(video_dir: str) -> dict:
    """Validate all videos in directory."""
    videos = VideoUtilities.list_videos(video_dir)
    results = {}
    
    logger.info(f"Validating {len(videos)} videos...")
    
    for video_name in videos:
        video_path = str(Path(video_dir) / video_name)
        try:
            info = VideoUtilities.get_video_info(video_path)
            results[video_name] = {
                'status': 'valid',
                'info': info
            }
            logger.info(f"   ✅ {video_name}: {info['total_frames']} frames @ {info['fps']} fps")
        except Exception as e:
            results[video_name] = {
                'status': 'error',
                'error': str(e)
            }
            logger.warning(f"   ❌ {video_name}: {e}")
    
    return results


def batch_validate_annotations(annotation_file: str, video_dir: str) -> dict:
    """Validate annotations against available videos."""
    logger.info("Validating annotations...")
    
    # Validate Excel format
    is_valid, errors = ExcelUtilities.validate_annotation_file(annotation_file)
    
    if not is_valid:
        logger.error(f"❌ Annotation file has errors:")
        for error in errors:
            logger.error(f"   - {error}")
        return {'valid': False, 'errors': errors}
    
    # Load annotations
    df = pd.read_excel(annotation_file)
    
    # Get available videos
    available_videos = set(VideoUtilities.list_videos(video_dir))
    
    # Check for missing videos
    annotation_videos = set(df['video_name'].unique())
    missing_videos = annotation_videos - available_videos
    
    result = {
        'valid': True,
        'total_annotations': len(df),
        'unique_videos': len(annotation_videos),
        'unique_persons': len(df['person_id'].unique()),
        'event_types': list(df['event_type'].unique()),
        'missing_videos': list(missing_videos) if missing_videos else []
    }
    
    if missing_videos:
        logger.warning(f"⚠️  Missing videos: {missing_videos}")
    else:
        logger.info(f"✅ All annotated videos found")
    
    logger.info(f"   Total annotations: {result['total_annotations']}")
    logger.info(f"   Videos: {result['unique_videos']}")
    logger.info(f"   People: {result['unique_persons']}")
    logger.info(f"   Event types: {result['event_types']}")
    
    return result


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Utilities for evaluation pipeline")
        print("Usage: python evaluation_utils.py <command> [args]")
        print("\nCommands:")
        print("  validate-videos <dir>              - Validate all videos in directory")
        print("  validate-annotations <file> <dir>  - Validate annotation file")
        print("  create-template <file>             - Create annotation template")
        print("  video-info <file>                  - Get video metadata")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'validate-videos':
        if len(sys.argv) < 3:
            print("Usage: python evaluation_utils.py validate-videos <dir>")
            sys.exit(1)
        results = batch_validate_videos(sys.argv[2])
        print(f"\nValidation complete: {sum(1 for r in results.values() if r['status'] == 'valid')}/{len(results)} valid")
    
    elif command == 'validate-annotations':
        if len(sys.argv) < 4:
            print("Usage: python evaluation_utils.py validate-annotations <file> <video_dir>")
            sys.exit(1)
        result = batch_validate_annotations(sys.argv[2], sys.argv[3])
        print(f"\n{result}")
    
    elif command == 'create-template':
        if len(sys.argv) < 3:
            print("Usage: python evaluation_utils.py create-template <output_file>")
            sys.exit(1)
        ExcelUtilities.create_empty_template(sys.argv[2])
    
    elif command == 'video-info':
        if len(sys.argv) < 3:
            print("Usage: python evaluation_utils.py video-info <file>")
            sys.exit(1)
        info = VideoUtilities.get_video_info(sys.argv[2])
        print(f"\nVideo Information:")
        for key, value in info.items():
            print(f"  {key}: {value}")
