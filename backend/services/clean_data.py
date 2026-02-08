"""
Data Cleaning Script for Virtue Foundation Ghana CSV
Cleans and preprocesses the CSV data before processing
"""

import pandas as pd
import json
import re
from pathlib import Path
from typing import List, Dict, Any

class DataCleaner:
    """Cleans healthcare facility data"""
    
    def __init__(self):
        self.required_columns = ['name', 'specialties', 'procedure', 'equipment', 
                                'address_city', 'address_country']
    
    def clean_json_field(self, value: Any) -> List[str]:
        """Parse JSON-like string fields into lists"""
        if pd.isna(value) or value is None or value == 'null':
            return []
        
        if isinstance(value, list):
            return value
        
        if isinstance(value, str):
            # Remove extra quotes and parse JSON
            value = value.strip()
            if value in ['[]', '', 'null', 'None']:
                return []
            
            try:
                # Try parsing as JSON
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if item]
                return [str(parsed).strip()] if parsed else []
            except json.JSONDecodeError:
                # If not JSON, split by common delimiters
                if ',' in value:
                    return [item.strip() for item in value.split(',') if item.strip()]
                return [value] if value else []
        
        return []
    
    def clean_text_field(self, value: Any, default: str = '') -> str:
        """Clean text fields with optional default"""
        if pd.isna(value) or value is None or value == 'null' or value == '':
            return default
        
        value = str(value).strip()
        if value.lower() in ['n/a', 'na', 'none', 'unknown', '--', 'null']:
            return default
        
        # Remove extra whitespace
        value = re.sub(r'\s+', ' ', value)
        return value if value else default
    
    def clean_phone_numbers(self, value: Any) -> List[str]:
        """Extract and clean phone numbers"""
        phones = self.clean_json_field(value)
        cleaned = []
        
        for phone in phones:
            # Remove common separators
            phone = re.sub(r'[\s\-\(\)]+', '', phone)
            # Keep only + and digits
            phone = re.sub(r'[^\d\+]', '', phone)
            if phone:
                cleaned.append(phone)
        
        return cleaned
    
    def deduplicate_facilities(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate facilities based on name and location"""
        print("   Deduplicating facilities...")
        
        initial_count = len(df)
        
        # Create composite key for deduplication
        df['_dedup_key'] = (
            df['name'].str.lower().str.strip() + '|' + 
            df['address_city'].fillna('').str.lower().str.strip()
        )
        
        # Keep first occurrence, prefer rows with more data
        df['_data_score'] = (
            df['specialties'].apply(lambda x: len(self.clean_json_field(x))) +
            df['procedure'].apply(lambda x: len(self.clean_json_field(x))) +
            df['equipment'].apply(lambda x: len(self.clean_json_field(x)))
        )
        
        # Sort by data score (descending) so most complete entries are kept
        df = df.sort_values('_data_score', ascending=False)
        df = df.drop_duplicates(subset='_dedup_key', keep='first')
        
        # Drop helper columns
        df = df.drop(columns=['_dedup_key', '_data_score'])
        
        final_count = len(df)
        print(f"   Removed {initial_count - final_count} duplicates ({initial_count} → {final_count})")
        
        return df
    
    def clean_csv(self, input_path: str, output_path: str = None, 
                  limit_rows: int = None) -> pd.DataFrame:
        """
        Clean CSV file and optionally save to new file
        
        Args:
            input_path: Path to input CSV
            output_path: Path to save cleaned CSV (optional)
            limit_rows: Limit to first N rows (for testing)
        
        Returns:
            Cleaned DataFrame
        """
        print(f"\n🧹 Cleaning CSV: {Path(input_path).name}")
        print("="*60)
        
        # Read CSV
        df = pd.read_csv(input_path)
        print(f"✓ Loaded {len(df)} rows, {len(df.columns)} columns")
        
        # Limit rows if specified
        if limit_rows:
            df = df.head(limit_rows)
            print(f"✓ Limited to first {limit_rows} rows for testing")
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        print(f"✓ Removed empty rows: {len(df)} rows remaining")
        
        # Clean key fields
        print("\n🔧 Cleaning fields...")
        
        # Clean name (required)
        df['name'] = df['name'].apply(self.clean_text_field)
        df = df[df['name'] != '']  # Remove rows without name
        print(f"   ✓ Cleaned 'name' field")
        
        # Clean location fields
        df['address_city'] = df['address_city'].apply(self.clean_text_field)
        df['address_country'] = df['address_country'].apply(self.clean_text_field)
        df['address_line1'] = df['address_line1'].apply(self.clean_text_field)
        df['address_line2'] = df['address_line2'].apply(self.clean_text_field)
        print(f"   ✓ Cleaned location fields")
        
        # Clean JSON array fields
        df['specialties'] = df['specialties'].apply(
            lambda x: json.dumps(self.clean_json_field(x))
        )
        df['procedure'] = df['procedure'].apply(
            lambda x: json.dumps(self.clean_json_field(x))
        )
        df['equipment'] = df['equipment'].apply(
            lambda x: json.dumps(self.clean_json_field(x))
        )
        df['capability'] = df['capability'].apply(
            lambda x: json.dumps(self.clean_json_field(x))
        )
        print(f"   ✓ Cleaned specialties, procedures, equipment, capabilities")
        
        # Clean contact fields
        df['phone_numbers'] = df['phone_numbers'].apply(
            lambda x: json.dumps(self.clean_phone_numbers(x))
        )
        df['email'] = df['email'].apply(self.clean_text_field)
        df['websites'] = df['websites'].apply(
            lambda x: json.dumps(self.clean_json_field(x))
        )
        print(f"   ✓ Cleaned contact fields")
        
        # Clean description
        df['description'] = df['description'].apply(self.clean_text_field)
        print(f"   ✓ Cleaned description field")
        
        # Deduplicate
        df = self.deduplicate_facilities(df)
        
        # Generate statistics
        print("\n📊 Cleaning Statistics:")
        print(f"   Final row count: {len(df)}")
        print(f"   Facilities with specialties: {sum(df['specialties'] != '[]')}")
        print(f"   Facilities with procedures: {sum(df['procedure'] != '[]')}")
        print(f"   Facilities with equipment: {sum(df['equipment'] != '[]')}")
        print(f"   Facilities with phone: {sum(df['phone_numbers'] != '[]')}")
        print(f"   Facilities with email: {sum(df['email'] != '')}")
        print(f"   Facilities with description: {sum(df['description'] != '')}")
        
        # City distribution
        city_counts = df['address_city'].value_counts().head(5)
        print(f"\n📍 Top 5 cities:")
        for city, count in city_counts.items():
            print(f"   {city}: {count} facilities")
        
        # Save if output path provided
        if output_path:
            df.to_csv(output_path, index=False)
            print(f"\n✅ Cleaned data saved to: {output_path}")
        
        return df


def main():
    """Clean the Virtue Foundation Ghana CSV"""
    
    # Paths
    input_csv = Path(__file__).parent / "data" / "Virtue Foundation Ghana v0.3 - Sheet1.csv"
    output_csv = Path(__file__).parent / "data" / "Virtue Foundation Ghana - CLEANED.csv"
    test_csv = Path(__file__).parent / "data" / "Virtue Foundation Ghana - TEST_20.csv"
    
    if not input_csv.exists():
        print(f"❌ Input file not found: {input_csv}")
        return
    
    # Create cleaner
    cleaner = DataCleaner()
    
    # Option 1: Clean first 20 rows for testing
    print("\n" + "="*60)
    print("  CREATING TEST DATASET (20 rows)")
    print("="*60)
    test_df = cleaner.clean_csv(str(input_csv), str(test_csv), limit_rows=20)
    
    # Option 2: Clean full dataset
    choice = input("\n🔧 Clean full dataset? (y/n): ").lower()
    if choice == 'y':
        print("\n" + "="*60)
        print("  CLEANING FULL DATASET")
        print("="*60)
        full_df = cleaner.clean_csv(str(input_csv), str(output_csv))
        print(f"\n🎉 Full dataset cleaned! Total rows: {len(full_df)}")
    else:
        print("\n✓ Skipped full dataset cleaning")
    
    print("\n✅ Data cleaning complete!")
    print(f"\n📁 Files created:")
    print(f"   Test (20 rows): {test_csv.name}")
    if choice == 'y':
        print(f"   Full dataset: {output_csv.name}")


if __name__ == "__main__":
    main()
