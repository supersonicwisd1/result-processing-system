# flask-app/app/extraction.py
from pypdf import PdfReader
from docx import Document
import csv
from openpyxl import load_workbook
from datetime import datetime

import tabula
from typing import Tuple, Dict, List
import re

def extract_docx_data(filepath):
    """Extract data from DOCX file format."""
    doc = Document(filepath)
    header_info = {
        "course_title": "",
        "course_code": "",
        "course_unit": 0,
        "department": "",
        "faculty": "",
        "semester": "",
        "session": "",
        "lecturers": ""
    }
    results_data = []
    
    # Process tables for both header and results
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            
            # Extract header information
            if len(cells) >= 2:
                first_cell = cells[0].strip()

                if "Title of Course" in first_cell:
                    # in the first cell which is named "Title of Course", the course title and course code are in the same cell
                    header_info["course_title"] = cells[1].strip()
                    header_info["course_code"] = cells[-1].strip()
                elif "Examination Date" in first_cell:
                    # in the first cell which is named "Examination Date", the course unit is in the last cell
                    try:
                        header_info["course_unit"] = int(cells[-1].strip())
                    except ValueError:
                        pass
                elif "Department" in first_cell:
                    # in the first cell which is named "Department", the department is in the second cell
                    header_info["department"] = cells[1].strip()
                    header_info["semester"] = cells[-1].strip()
                elif "Faculty" in first_cell:
                    # in the first cell which is named "Faculty", the faculty is in the second cell
                    header_info["faculty"] = cells[1].strip()  
                    header_info["session"] = cells[-1].strip()           
                elif "Name of Lecturers" in first_cell:
                    # in the first cell which is named "Name of Lecturers", the lecturers are in the second cell
                    header_info["lecturers"] = cells[1].strip()
            
            # Extract student results
            if len(cells) >= 7 and any("/" in cell for cell in cells):
                try:
                    # Find registration number column
                    reg_idx = next(i for i, cell in enumerate(cells) if "/" in cell)
                    results_data.append({
                        "name": cells[0].strip(),  # Name is always first column
                        "registration_number": cells[reg_idx].strip(),
                        "department": cells[reg_idx + 1].strip(),
                        "level": "100",
                        "continuous_assessment": float(cells[reg_idx + 3].strip()),
                        "exam_score": float(cells[reg_idx + 4].strip()),
                        "total_score": float(cells[reg_idx + 5].strip()),
                        "grade": cells[reg_idx + 6].strip()
                    })
                except (ValueError, IndexError) as e:
                    print(f"Error processing row in DOCX: {e}")
                    continue

    print("Docx Result \n", header_info, "\n\n\n\n" ,results_data, "\n\n\n\n")
    return header_info, results_data

def extract_pdf_data(filepath: str) -> Tuple[Dict, List]:
    """Extract data from PDF using PyPDF Reader."""
    header_info = {
        "course_title": "",
        "course_code": "",
        "course_unit": 0,
        "department": "",
        "faculty": "",
        "semester": "",
        "session": "",
        "lecturers": ""
    }
    results_data = []
    
    try:
        with open(filepath, 'rb') as file:
            reader = PdfReader(file)
            first_page = reader.pages[0].extract_text()
            
            # Preprocess text to handle line breaks and split words
            lines = first_page.split('\n')
            
            # Extract header information with improved patterns
            for line in lines:
                if "Title of Course:" in line:
                    match = re.search(r"Title of Course:\s*([\w\s]+)\s*Course Code:(\w+)", line)
                    if match:
                        header_info["course_title"] = match.group(1).strip()
                        header_info["course_code"] = match.group(2).strip()
                
                elif "Course Unit:" in line:
                    match = re.search(r"Course Unit:(\d+)", line)
                    if match:
                        header_info["course_unit"] = int(match.group(1))
                
                elif "Department:" in line:
                    match = re.search(r"Department:\s*([\w\s]+)\s*Semester:", line)
                    if match:
                        header_info["department"] = match.group(1).strip()
                
                elif "Faculty:" in line:
                    match = re.search(r"Faculty:\s*([\w\s]+)\s*Session:", line)
                    if match:
                        header_info["faculty"] = match.group(1).strip()
                
                elif "Semester:" in line:
                    match = re.search(r"Semester:\s*([\w\s]+)", line)
                    if match:
                        header_info["semester"] = match.group(1).strip()
                
                elif "Session:" in line:
                    match = re.search(r"Session:(\d+/\d+)", line)
                    if match:
                        header_info["session"] = match.group(1).strip()
                
                elif "Name of Lecturers:" in line:
                    match = re.search(r"Name of Lecturers:\s*(.*?)\s*Page", line)
                    if match:
                        header_info["lecturers"] = match.group(1).strip()

            # Process results
            results_section = False
            for line in lines:
                if "Names" in line:
                    results_section = True
                    continue
                
                if results_section and "2019/" in line:
                    # Split line into components
                    parts = re.split(r'\s+', line.strip())
                    try:
                        # Find registration number index
                        reg_idx = next(i for i, part in enumerate(parts) if "2019/" in part)
                        
                        # Extract name by joining all parts before registration number
                        name = " ".join(parts[:reg_idx])
                        
                        # Extract other fields
                        reg_no = parts[reg_idx]
                        dept = "COMPUTER SCIENCE"  # Default value since it's consistent
                        
                        # Find scores and grade
                        scores = [part for part in parts[reg_idx+1:] if part.replace('.', '').isdigit()]
                        grade = parts[-1] if parts[-1] in ['A', 'B', 'C', 'D', 'E', 'F'] else None
                        
                        if len(scores) >= 3 and grade:
                            results_data.append({
                                "name": name.strip(),
                                "registration_number": reg_no.strip(),
                                "department": dept.strip(),
                                "level": "100",
                                "continuous_assessment": float(scores[-3]),
                                "exam_score": float(scores[-2]),
                                "total_score": float(scores[-1]),
                                "grade": grade
                            })
                    except (ValueError, IndexError) as e:
                        print(f"Error processing line: {line}")
                        print(f"Error details: {e}")
                        continue

    except Exception as e:
        print(f"Error extracting data from PDF: {e}")
    
    print("PDF Extraction Results:")
    print("Header Info:", header_info)
    print("\nResults Data:", results_data)
    
    return header_info, results_data

def extract_csv_data(filepath):
    """Extract data from CSV file format."""
    header_info = {
        "course_title": "",
        "course_code": "",
        "course_unit": 0,
        "department": "",
        "faculty": "",
        "semester": "",
        "session": "",
        "lecturers": ""
    }
    results_data = []
    
    with open(filepath, newline='') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)
        
        # Process header information from first few rows
        for row in rows[:8]:  # First 8 rows contain header info
            if len(row) >= 2:
                first_col = row[0].strip()
                if "Title of Course" in first_col:
                    header_info["course_title"] = row[1].strip()
                elif "Course Code" in first_col:
                    header_info["course_code"] = row[-1].strip()
                elif "Course Unit" in first_col:
                    try:
                        header_info["course_unit"] = int(row[-1].strip())
                    except ValueError:
                        pass
                elif "Department" in first_col:
                    header_info["department"] = row[1].strip()
                elif "Faculty" in first_col:
                    header_info["faculty"] = row[1].strip()
                elif "Semester" in first_col:
                    header_info["semester"] = row[-1].strip()
                elif "Session" in first_col:
                    header_info["session"] = row[-1].strip()
                elif "Name of Lecturers" in first_col:
                    header_info["lecturers"] = row[1].strip()
        
        # Find the start of student data
        try:
            header_row_idx = next(i for i, row in enumerate(rows) if "Names" in row[0])
            
            # Process student results
            for row in rows[header_row_idx + 1:]:
                if len(row) >= 8 and "2019/" in row[1]:  # Ensure we have all required columns
                    try:
                        results_data.append({
                            "name": row[0].strip(),
                            "registration_number": row[1].strip(),
                            "department": row[2].strip(),
                            "level": row[3].strip(),
                            "continuous_assessment": float(row[4].strip()),
                            "exam_score": float(row[5].strip()),
                            "total_score": float(row[6].strip()),
                            "grade": row[7].strip()
                        })
                    except (ValueError, IndexError) as e:
                        print(f"Error processing row in CSV: {e}")
                        continue
        except StopIteration:
            print("Could not find header row in CSV file")
    print("CSV Result \n", header_info, "\n\n\n\n" ,results_data, "\n\n\n\n")
    return header_info, results_data

def extract_xlsx_data(filepath):
    """Extract data from XLSX file format."""
    header_info = {
        "course_title": "",
        "course_code": "",
        "course_unit": 0,
        "department": "",
        "faculty": "",
        "semester": "",
        "session": "",
        "lecturers": ""
    }
    results_data = []
    
    workbook = load_workbook(filepath)
    sheet = workbook.active
    rows = list(sheet.values)
    
    # Process header information
    for row in rows[:8]:
        if row and len(row) >= 2:
            first_col = str(row[0]).strip()
            if "Title of Course" in first_col:
                header_info["course_title"] = str(row[1]).strip()
            elif "Course Code" in first_col:
                header_info["course_code"] = str(row[-1]).strip()
            elif "Course Unit" in first_col:
                try:
                    header_info["course_unit"] = int(str(row[-1]).strip())
                except ValueError:
                    pass
            elif "Department" in first_col:
                header_info["department"] = str(row[1]).strip()
            elif "Faculty" in first_col:
                header_info["faculty"] = str(row[1]).strip()
            elif "Semester" in first_col:
                header_info["semester"] = str(row[-1]).strip()
            elif "Session" in first_col:
                header_info["session"] = str(row[-1]).strip()
            elif "Name of Lecturers" in first_col:
                header_info["lecturers"] = str(row[1]).strip()
    
    # Find header row
    try:
        header_row_idx = next(i for i, row in enumerate(rows) if row and "Names" in str(row[0]))
        
        # Process student results
        for row in rows[header_row_idx + 1:]:
            if row and len(row) >= 8 and "2019/" in str(row[1]):
                try:
                    results_data.append({
                        "name": str(row[0]).strip(),
                        "registration_number": str(row[1]).strip(),
                        "department": str(row[2]).strip(),
                        "level": str(row[3]).strip(),
                        "continuous_assessment": float(str(row[4]).strip()),
                        "exam_score": float(str(row[5]).strip()),
                        "total_score": float(str(row[6]).strip()),
                        "grade": str(row[7]).strip()
                    })
                except (ValueError, IndexError) as e:
                    print(f"Error processing row in XLSX: {e}")
                    continue
    except StopIteration:
        print("Could not find header row in XLSX file")

    return header_info, results_data

def process_extracted_data(header_info, results_data, original_filename, uploader_id):
    """Process extracted data into format ready for database insertion."""
    processed_data = {
        "course_info": {
            "code": header_info["course_code"],
            "title": header_info["course_title"],
            "unit": header_info["course_unit"],
            "department": header_info["department"],
            "faculty": header_info["faculty"],
            "level": "100"
        },
        "semester_info": {
            "name": header_info["semester"]
        },
        "results": []
    }
    
    for result in results_data:
        processed_result = {
            "student": {
                "registration_number": result["registration_number"],
                "name": result["name"],
                "department": result["department"]
            },
            "result": {
                "continuous_assessment": result["continuous_assessment"],
                "exam_score": result["exam_score"],
                "total_score": result["total_score"],
                "grade": result["grade"],
                "original_file": original_filename,
                "upload_date": datetime.utcnow(),
                "uploader_lecturer_id": uploader_id
            }
        }
        processed_data["results"].append(processed_result)
    
    return processed_data

