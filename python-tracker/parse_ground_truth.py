"""
Parse ground truth annotations from Excel files.
Converts timestamps to milliseconds and structures data for evaluation.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GroundTruthParser:
    """Parse and structure ground truth annotations from Excel files."""
    
    def __init__(self, annotations_file: str):
        """
        Initialize parser with annotations Excel file.
        
        Args:
            annotations_file: Path to Excel file with columns:
                [video_name, timestamp, event_type, person_id, bbox]
        """
        self.annotations_file = annotations_file
        self.df = None
        self.ground_truth = {}
        self.video_metadata = {}
        
    def load_annotations(self) -> pd.DataFrame:
        """Load annotations from Excel file."""
        try:
            self.df = pd.read_excel(self.annotations_file)
            logger.info(f"✅ Loaded {len(self.df)} annotations from {self.annotations_file}")
            logger.info(f"   Columns: {list(self.df.columns)}")
            return self.df
        except FileNotFoundError:
            logger.error(f"❌ File not found: {self.annotations_file}")
            raise
        except Exception as e:
            logger.error(f"❌ Error loading Excel file: {e}")
            raise
    
    def _time_to_milliseconds(self, time_str: str) -> int:
        """
        Convert time string (HH:MM:SS.sss) to milliseconds.
        
        Args:
            time_str: Time in format "HH:MM:SS" or "HH:MM:SS.sss"
            
        Returns:
            Time in milliseconds as integer
        """
        try:
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            
            total_ms = int((hours * 3600 + minutes * 60 + seconds) * 1000)
            return total_ms
        except (ValueError, IndexError) as e:
            logger.warning(f"⚠️  Could not parse timestamp '{time_str}': {e}")
            return 0
    
    def _parse_bbox(self, bbox_str: str) -> List[float]:
        """
        Parse bounding box from string format.
        
        Args:
            bbox_str: Bounding box in format "[x1,y1,x2,y2]" or "x1,y1,x2,y2"
            
        Returns:
            List of [x1, y1, x2, y2] as floats
        """
        try:
            # Remove brackets if present
            bbox_str = str(bbox_str).strip('[]')
            coords = [float(x.strip()) for x in bbox_str.split(',')]
            
            if len(coords) != 4:
                logger.warning(f"⚠️  Invalid bbox format: {bbox_str}")
                return None
            
            return coords
        except ValueError as e:
            logger.warning(f"⚠️  Could not parse bbox '{bbox_str}': {e}")
            return None
    
    def parse_ground_truth(self) -> Dict:
        """
        Parse ground truth annotations into structured format.
        
        Returns:
            Dictionary with structure:
            {
                'video_name.mp4': {
                    'frames': {
                        frame_ms: [
                            {
                                'timestamp_ms': int,
                                'event_type': str,
                                'person_id': str,
                                'bbox': [x1, y1, x2, y2],
                                'area': float
                            },
                            ...
                        ],
                        ...
                    },
                    'total_annotations': int
                },
                ...
            }
        """
        if self.df is None:
            self.load_annotations()
        
        ground_truth = {}
        
        for idx, row in self.df.iterrows():
            video_name = str(row['video_name']).strip()
            timestamp_str = str(row['timestamp']).strip()
            event_type = str(row['event_type']).strip().upper()
            person_id = str(row['person_id']).strip()
            bbox_str = row['bbox']
            
            # Convert timestamp to milliseconds
            timestamp_ms = self._time_to_milliseconds(timestamp_str)
            
            # Parse bounding box
            bbox = self._parse_bbox(bbox_str)
            if bbox is None:
                logger.warning(f"   Skipping row {idx} due to invalid bbox")
                continue
            
            # Calculate bbox area
            x1, y1, x2, y2 = bbox
            area = (x2 - x1) * (y2 - y1)
            
            # Initialize video entry if needed
            if video_name not in ground_truth:
                ground_truth[video_name] = {
                    'frames': {},
                    'total_annotations': 0,
                    'event_types': set()
                }
            
            # Add annotation to frame
            if timestamp_ms not in ground_truth[video_name]['frames']:
                ground_truth[video_name]['frames'][timestamp_ms] = []
            
            annotation = {
                'timestamp_ms': timestamp_ms,
                'event_type': event_type,
                'person_id': person_id,
                'bbox': bbox,
                'area': area
            }
            
            ground_truth[video_name]['frames'][timestamp_ms].append(annotation)
            ground_truth[video_name]['total_annotations'] += 1
            ground_truth[video_name]['event_types'].add(event_type)
        
        # Convert sets to lists for serialization
        for video in ground_truth:
            ground_truth[video]['event_types'] = list(ground_truth[video]['event_types'])
        
        self.ground_truth = ground_truth
        
        logger.info(f"\n📊 Ground Truth Summary:")
        logger.info(f"   Total videos: {len(ground_truth)}")
        for video_name, data in ground_truth.items():
            logger.info(f"   {video_name}:")
            logger.info(f"      - Annotations: {data['total_annotations']}")
            logger.info(f"      - Event types: {data['event_types']}")
            logger.info(f"      - Frames with annotations: {len(data['frames'])}")
        
        return ground_truth
    
    def get_video_ground_truth(self, video_name: str) -> Dict:
        """Get ground truth for specific video."""
        return self.ground_truth.get(video_name, None)
    
    def get_frame_annotations(self, video_name: str, frame_ms: int, tolerance_ms: int = 50) -> List[Dict]:
        """
        Get annotations for a frame, with tolerance window.
        
        Args:
            video_name: Name of video file
            frame_ms: Frame timestamp in milliseconds
            tolerance_ms: Time window tolerance (+/- ms)
            
        Returns:
            List of annotations within tolerance window
        """
        if video_name not in self.ground_truth:
            return []
        
        annotations = []
        frames = self.ground_truth[video_name]['frames']
        
        for anno_ms, annos in frames.items():
            if abs(anno_ms - frame_ms) <= tolerance_ms:
                annotations.extend(annos)
        
        return annotations
    
    def export_to_csv(self, output_file: str):
        """Export parsed ground truth to CSV for inspection."""
        rows = []
        
        for video_name, data in self.ground_truth.items():
            for frame_ms, annotations in data['frames'].items():
                for anno in annotations:
                    rows.append({
                        'video_name': video_name,
                        'timestamp_ms': anno['timestamp_ms'],
                        'timestamp_sec': anno['timestamp_ms'] / 1000.0,
                        'event_type': anno['event_type'],
                        'person_id': anno['person_id'],
                        'x1': anno['bbox'][0],
                        'y1': anno['bbox'][1],
                        'x2': anno['bbox'][2],
                        'y2': anno['bbox'][3],
                        'area': anno['area']
                    })
        
        df_export = pd.DataFrame(rows)
        df_export.to_csv(output_file, index=False)
        logger.info(f"✅ Exported parsed ground truth to {output_file}")


def create_sample_annotation_file(output_file: str):
    """Create a sample annotation Excel file for reference."""
    sample_data = {
        'video_name': ['video1.mp4', 'video1.mp4', 'video1.mp4', 'video2.mp4'],
        'timestamp': ['00:00:05', '00:00:07', '00:00:10', '00:00:15'],
        'event_type': ['ENTRY', 'ENTRY', 'EXIT', 'ENTRY'],
        'person_id': ['person_1', 'person_2', 'person_1', 'person_3'],
        'bbox': [
            '[100,50,200,300]',
            '[150,60,220,310]',
            '[105,55,205,305]',
            '[80,40,180,280]'
        ]
    }
    
    df = pd.DataFrame(sample_data)
    df.to_excel(output_file, index=False)
    logger.info(f"✅ Created sample annotation file: {output_file}")


if __name__ == '__main__':
    # Example usage
    import sys
    
    # Create sample file
    create_sample_annotation_file('sample_annotations.xlsx')
    
    # Parse ground truth
    parser = GroundTruthParser('sample_annotations.xlsx')
    parser.load_annotations()
    ground_truth = parser.parse_ground_truth()
    
    # Export to CSV
    parser.export_to_csv('parsed_ground_truth.csv')
    
    print("\n✅ Ground truth parsing completed!")
