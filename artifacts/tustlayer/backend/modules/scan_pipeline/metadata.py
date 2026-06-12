from PIL import Image, ExifTags
import io

class MetadataService:
    def __init__(self):
        # Broad list of image editors and fraud utilities
        self.suspicious_software = [
            "photoshop", "canva", "lightroom", "gimp", "picsart", 
            "pixelmator", "snapseed", "figma", "sketch", "photoroom", 
            "inshot", "pixlr", "meitu", "snapseed", "befunky", "fotor",
            "gd-jpeg", "paint.net", "canvas"
        ]

    def extract_anomalies(self, image_bytes: bytes) -> int:
        """
        Performs deep forensic scanning of image EXIF tags and file metadata info blocks.
        Returns the number of detected anomalies (red flags).
        """
        anomalies = 0
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # 1. Check EXIF tags
            exif_data = image.getexif() if hasattr(image, "getexif") else None
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                    tag_name_str = str(tag_name).lower()
                    value_str = str(value).lower()
                    
                    # Inspect software, designer, or comments tags
                    if any(t in tag_name_str for t in ["software", "software", "comment", "artist", "copyright"]):
                        if any(susp in value_str for susp in self.suspicious_software):
                            print(f"[METADATA-FORENSICS] EXIF anomaly detected: {tag_name} = {value}")
                            anomalies += 2

            # 2. Check PIL image.info metadata blocks (highly reliable for PNG/JPEG comments and text chunks)
            info = image.info or {}
            for key, val in info.items():
                key_str = str(key).lower()
                val_str = str(val).lower()
                
                # Check for software / creator metadata referencing editors
                if any(k in key_str for k in ["software", "comment", "description", "source", "author", "creation time"]):
                    if any(susp in val_str for susp in self.suspicious_software):
                        print(f"[METADATA-FORENSICS] Info Block anomaly detected: {key} = {val}")
                        anomalies += 2
                
                # Direct check on any text string containing editing tool names
                if any(susp in val_str for susp in self.suspicious_software):
                    print(f"[METADATA-FORENSICS] String block references editor: {val}")
                    anomalies += 2
                    
        except Exception as e:
            print(f"Metadata Forensic Scan Warning: {e}")
            
        return anomalies
