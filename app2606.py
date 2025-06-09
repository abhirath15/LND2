# app.py - Enhanced Interactive Learning Path Advisor with AI Search & Udemy Integration

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import google.generativeai as genai
from PIL import Image
import numpy as np
import time
import re
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
import requests
from urllib.parse import quote_plus
import asyncio
import aiohttp
import uuid
import plotly.express as px  # Add this import for charts

# Set page configuration
st.set_page_config(
    page_title="Smart Learning Path Advisor",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Multiselect widget */
    .stMultiSelect > div > div > div > div {
       
        border-color: #1f77b4 !important;
    }
    
    /* Multiselect selected items */
    .stMultiSelect > div > div > div > div > span {
        background-color: #1f77b4 !important;
        border-color: #1f77b4 !important;
    }
    
    /* Selectbox */
    .stSelectbox > div > div > select {
        border-color: #1f77b4 !important;
    }
    
    .stSelectbox > div > div > select:focus {
        border-color: #1f77b4 !important;
        box-shadow: 0 0 0 0.2rem rgba(31, 119, 180, 0.25) !important;
    }
    
    /* Radio buttons */
    .stRadio > div > label > div:first-child {
        background-color: #1f77b4 !important;
        border-color: #1f77b4 !important;
    }
    
    /* Checkboxes */
    .stCheckbox > label > div:first-child {
        background-color: #1f77b4 !important;
        border-color: #1f77b4 !important;
    }
    
    /* Slider */
    .stSlider > div > div > div > div {
        background-color: #1f77b4 !important;
    }
    
    /* Text input focus */
    .stTextInput > div > div > input:focus {
        border-color: #1f77b4 !important;
        box-shadow: 0 0 0 0.2rem rgba(31, 119, 180, 0.25) !important;
    }
    
    /* Number input focus */
    .stNumberInput > div > div > input:focus {
        border-color: #1f77b4 !important;
        box-shadow: 0 0 0 0.2rem rgba(31, 119, 180, 0.25) !important;
    }
    
    /* Date input focus */
    .stDateInput > div > div > input:focus {
        border-color: #1f77b4 !important;
        box-shadow: 0 0 0 0.2rem rgba(31, 119, 180, 0.25) !important;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #1f77b4 !important;
        border-color: #1f77b4 !important;
        color: white !important;
    }
    
    .stButton > button:hover {
        background-color: #145a8a !important;
        border-color: #145a8a !important;
    }
    
    /* Download button */
    .stDownloadButton > button {
        background-color: #1f77b4 !important;
        border-color: #1f77b4 !important;
        color: white !important;
    }
    
    .stDownloadButton > button:hover {
        background-color: #145a8a !important;
        border-color: #145a8a !important;
    }
</style>
""", unsafe_allow_html=True)




# Data classes for structured data
@dataclass
class LearningPreference:
    time_available_weeks: int = 8
    preferred_learning_style: str = "Mixed"  # Visual, Auditory, Hands-on, Mixed
    difficulty_preference: str = "Progressive"  # Beginner, Intermediate, Advanced, Progressive
    specific_skills_requested: List[str] = None
    learning_urgency: str = "Medium"  # Low, Medium, High, Critical

@dataclass
class LearningGoal:
    goal_type: str  # skill_development, role_transition, certification, project_based
    target_skill: str = ""
    target_role: str = ""
    deadline: Optional[datetime] = None
    priority: str = "Medium"

@dataclass
class UdemyCourse:
    title: str
    url: str
    description: str
    rating: float
    price: str
    duration: str
    level: str

# Enhanced session state initialization
def initialize_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm your enhanced learning advisor with AI-powered search capabilities. How can I assist you today?"}
        ]

    if 'learning_path' not in st.session_state:
        st.session_state.learning_path = None

    if 'employee_profile' not in st.session_state:
        st.session_state.employee_profile = {
            "employee_id": "EMP123456",
            "name": "Aditya Gupta",
            "current_role": "Data Analyst",
            "skills": ["SQL", "Excel", "Data Visualization", "Python"],
            "completed_courses": ["Data Analysis Fundamentals", "Excel Advanced", "SQL Intermediate"],
            "career_goals": ["Senior Data Analyst"], # Changed to list for consistency
            "skill_proficiency": {
                "SQL": "Intermediate",
                "Excel": "Advanced", 
                "Data Visualization": "Intermediate",
                "Python": "Beginner"
            },
            "experience_level": "Mid-level",
        }
    
    if 'learning_preferences' not in st.session_state:
        st.session_state.learning_preferences = LearningPreference(
            specific_skills_requested=[]
        )
    
    if 'current_learning_goals' not in st.session_state:
        st.session_state.current_learning_goals = []

    if 'search_cache' not in st.session_state:
        st.session_state.search_cache = {}

    if 'page' not in st.session_state:
        st.session_state.page = "Employee Portal" # Default page

    if 'learning_path_progress' not in st.session_state:
        # Stores progress: {employee_id: {course_id: {"status": "Not Started", "start_date": None, "completion_date": None}}}
        st.session_state.learning_path_progress = {}

    if 'saved_learning_paths_file' not in st.session_state:
        st.session_state.saved_learning_paths_file = "learning_paths_data.json"


initialize_session_state()

# 2. Add employee database management functions after initialize_session_state()

@st.cache_data
def load_employee_database():
    """Load employee database with sample data"""
    return {
        "EMP123456": {
            "employee_id": "EMP123456",
            "name": "Aditya Gupta",
            "current_role": "Data Analyst",
            "skills": ["SQL", "Excel", "Data Visualization", "Python"],
            "completed_courses": ["Data Analysis Fundamentals", "Excel Advanced", "SQL Intermediate"],
            "career_goals": ["Senior Data Analyst"],
            "skill_proficiency": {
                "SQL": "Intermediate",
                "Excel": "Advanced", 
                "Data Visualization": "Intermediate",
                "Python": "Beginner"
            },
            "experience_level": "Mid-level",
            "manager_id": "MGR001",
            "department": "Analytics",
            "assigned_learning_path": None
        },
        "EMP789012": {
            "employee_id": "EMP789012",
            "name": "Ankita Sharma",
            "current_role": "Junior Data Analyst",
            "skills": ["Excel", "Python", "SQL"],
            "completed_courses": ["Data Analysis Fundamentals", "Python Basics"],
            "career_goals": ["Data Analyst"],
            "skill_proficiency": {
                "Excel": "Intermediate",
                "Python": "Beginner",
                "SQL": "Beginner"
            },
            "experience_level": "Junior",
            "manager_id": "MGR001",
            "department": "Analytics",
            "assigned_learning_path": None
        },
        "EMP345678": {
            "employee_id": "EMP345678",
            "name": "Rohit Verma",
            "current_role": "Business Analyst",
            "skills": ["Excel", "SQL", "Data Analysis"],
            "completed_courses": ["Business Analysis Fundamentals", "SQL Basics"],
            "career_goals": ["Senior Business Analyst"],
            "skill_proficiency": {
                "Excel": "Advanced",
                "SQL": "Intermediate",
                "Data Analysis": "Intermediate"
            },
            "experience_level": "Mid-level",
            "manager_id": "MGR001",
            "department": "Business",
            "assigned_learning_path": None
        },
        "EMP999000": {
            "employee_id": "EMP999000",
            "name": "Ritesh Kumar",
            "current_role": "Software Engineer",
            "skills": ["Python", "Java", "SQL", "Git"],
            "completed_courses": ["Object-Oriented Programming", "Database Design"],
            "career_goals": ["Senior Software Engineer"],
            "skill_proficiency": {
                "Python": "Intermediate",
                "Java": "Intermediate",
                "SQL": "Intermediate",
                "Git": "Advanced"
            },
            "experience_level": "Mid-level",
            "manager_id": "MGR002",
            "department": "Engineering",
            "assigned_learning_path": None
        },
        "EMP556677": {
            "employee_id": "EMP556677",
            "name": "Priya Patel",
            "current_role": "Data Scientist",
            "skills": ["Python", "Machine Learning", "Statistics", "SQL", "Data Visualization"],
            "completed_courses": ["Machine Learning Fundamentals", "Statistical Analysis", "Deep Learning Basics"],
            "career_goals": ["Senior Data Scientist"],
            "skill_proficiency": {
                "Python": "Advanced",
                "Machine Learning": "Intermediate",
                "Statistics": "Advanced",
                "SQL": "Advanced",
                "Data Visualization": "Intermediate"
            },
            "experience_level": "Mid-level",
            "manager_id": "MGR003",
            "department": "Data Science",
            "assigned_learning_path": None
        },
        "EMP778899": {
            "employee_id": "EMP778899",
            "name": "Arjun Singh",
            "current_role": "Junior Software Engineer",
            "skills": ["Python", "Git", "Data Structures"],
            "completed_courses": ["Programming Fundamentals", "Version Control"],
            "career_goals": ["Software Engineer"],
            "skill_proficiency": {
                "Python": "Intermediate",
                "Git": "Intermediate",
                "Data Structures": "Beginner"
            },
            "experience_level": "Junior",
            "manager_id": "MGR002",
            "department": "Engineering",
            "assigned_learning_path": None
        },
        "EMP334455": {
            "employee_id": "EMP334455",
            "name": "Sneha Reddy",
            "current_role": "DevOps Engineer",
            "skills": ["Linux", "Docker", "CI/CD", "AWS"],
            "completed_courses": ["Linux Administration", "Docker Essentials", "AWS Fundamentals"],
            "career_goals": ["Senior DevOps Engineer"],
            "skill_proficiency": {
                "Linux": "Advanced",
                "Docker": "Intermediate",
                "CI/CD": "Intermediate",
                "AWS": "Intermediate"
            },
            "experience_level": "Mid-level",
            "manager_id": "MGR004",
            "department": "Infrastructure",
            "assigned_learning_path": None
        },
        "EMP667788": {
            "employee_id": "EMP667788",
            "name": "Vikram Joshi",
            "current_role": "Frontend Developer",
            "skills": ["JavaScript", "React", "HTML", "CSS"],
            "completed_courses": ["Web Development Fundamentals", "React Basics"],
            "career_goals": ["Senior Frontend Developer"],
            "skill_proficiency": {
                "JavaScript": "Intermediate",
                "React": "Intermediate",
                "HTML": "Advanced",
                "CSS": "Advanced"
            },
            "experience_level": "Mid-level",
            "manager_id": "MGR002",
            "department": "Engineering",
            "assigned_learning_path": None
        },
        "EMP112233": {
            "employee_id": "EMP112233",
            "name": "Kavya Nair",
            "current_role": "Data Engineer",
            "skills": ["Python", "SQL", "ETL", "Apache Spark"],
            "completed_courses": ["Data Engineering Fundamentals", "Big Data Processing"],
            "career_goals": ["Senior Data Engineer"],
            "skill_proficiency": {
                "Python": "Advanced",
                "SQL": "Advanced",
                "ETL": "Intermediate",
                "Apache Spark": "Intermediate"
            },
            "experience_level": "Mid-level",
            "manager_id": "MGR003",
            "department": "Data Engineering",
            "assigned_learning_path": None
        },
        "EMP445566": {
            "employee_id": "EMP445566",
            "name": "Rahul Agarwal",
            "current_role": "QA Engineer",
            "skills": ["Testing", "Selenium", "Bug Tracking", "API Testing"],
            "completed_courses": ["Software Testing Fundamentals", "Test Automation"],
            "career_goals": ["Senior QA Engineer"],
            "skill_proficiency": {
                "Testing": "Advanced",
                "Selenium": "Intermediate",
                "Bug Tracking": "Advanced",
                "API Testing": "Intermediate"
            },
            "experience_level": "Mid-level",
            "manager_id": "MGR002",
            "department": "Quality Assurance",
            "assigned_learning_path": None
        },
        "EMP887766": {
            "employee_id": "EMP887766",
            "name": "Meera Krishnan",
            "current_role": "Senior Data Scientist",
            "skills": ["Machine Learning", "Deep Learning", "Python", "MLOps", "Research"],
            "completed_courses": ["Advanced Machine Learning", "Deep Learning Specialization", "MLOps Pipeline"],
            "career_goals": ["Principal Data Scientist"],
            "skill_proficiency": {
                "Machine Learning": "Advanced",
                "Deep Learning": "Advanced",
                "Python": "Expert",
                "MLOps": "Intermediate",
                "Research": "Advanced"
            },
            "experience_level": "Senior",
            "manager_id": "MGR003",
            "department": "Data Science",
            "assigned_learning_path": None
        },
        "EMP998877": {
            "employee_id": "EMP998877",
            "name": "Amit Gupta",
            "current_role": "Senior Software Engineer",
            "skills": ["System Design", "Python", "Java", "Cloud Architecture", "Team Leadership"],
            "completed_courses": ["System Design Mastery", "Cloud Architecture", "Leadership Essentials"],
            "career_goals": ["Tech Lead"],
            "skill_proficiency": {
                "System Design": "Advanced",
                "Python": "Expert",
                "Java": "Advanced",
                "Cloud Architecture": "Intermediate",
                "Team Leadership": "Intermediate"
            },
            "experience_level": "Senior",
            "manager_id": "MGR002",
            "department": "Engineering",
            "assigned_learning_path": None
        }
    }


def initialize_manager_session_state():
    """Initialize manager-specific session state"""
    if 'employee_database' not in st.session_state:
        st.session_state.employee_database = load_employee_database()
    
    if 'current_manager_id' not in st.session_state:
        st.session_state.current_manager_id = "MGR001" # Default manager
    
    if 'selected_employee_id' not in st.session_state:
        st.session_state.selected_employee_id = None
    
    if 'manager_mode' not in st.session_state:
        st.session_state.manager_mode = False
    
    if 'admin_mode' not in st.session_state: # Initialize admin mode
        st.session_state.admin_mode = False
    
    if 'selected_admin_employees' not in st.session_state: # For multi-select in admin portal
        st.session_state.selected_admin_employees = []

# 3. Add manager portal functions

def get_manager_employees(manager_id):
    """Get all employees under a specific manager"""
    return {emp_id: emp_data for emp_id, emp_data in st.session_state.employee_database.items() 
            if emp_data.get('manager_id') == manager_id}

def update_employee_in_database(employee_id, updated_profile):
    """Update employee profile in database"""
    if employee_id in st.session_state.employee_database:
        st.session_state.employee_database[employee_id].update(updated_profile)
        return True
    return False

def assign_learning_path_to_employee(employee_id, learning_path):
    """Assign a learning path to an employee"""
    if employee_id in st.session_state.employee_database:
        st.session_state.employee_database[employee_id]['assigned_learning_path'] = learning_path
        return True
    return False

# 4. Add manager portal page function

def manager_portal_page():
    st.title("👨‍💼 Manager Portal - Learning Path Management")
    st.markdown("*Manage your team's learning and development*")
    
    # Manager info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Manager ID", st.session_state.current_manager_id)
    with col2:
        manager_employees = get_manager_employees(st.session_state.current_manager_id)
        st.metric("Team Size", len(manager_employees))
    with col3:
        employees_with_paths = sum(1 for emp in manager_employees.values() 
                                 if emp.get('assigned_learning_path') is not None)
        st.metric("Active Learning Paths", employees_with_paths)
    
    # Employee selection
    st.markdown("### 👥 Select Employee")
    
    if not manager_employees:
        st.warning("No employees found under your management.")
        return
    
    # Employee selection dropdown
    employee_options = {f"{emp_data['name']} ({emp_id})": emp_id 
                       for emp_id, emp_data in manager_employees.items()}
    
    selected_employee_display = st.selectbox(
        "Choose an employee to manage:",
        options=list(employee_options.keys()),
        key="employee_selector"
    )
    
    if selected_employee_display:
        
        selected_employee_id = employee_options[selected_employee_display]
        st.session_state.selected_employee_id = selected_employee_id
        
        # Load selected employee data
        employee_data = st.session_state.employee_database[selected_employee_id]
        
        # Display employee information in tabs
        tab1, tab2, tab3 = st.tabs(["📋 Employee Profile", "🎯 Generate Learning Path", "📚 Assigned Learning Path"])
        
        with tab1:
            display_and_edit_employee_profile(selected_employee_id, employee_data)
        
        with tab2:
            generate_learning_path_for_employee(selected_employee_id, employee_data)
        
        with tab3:
            display_assigned_learning_path(selected_employee_id, employee_data)

def display_and_edit_employee_profile(employee_id, employee_data):
    """Display and allow editing of employee profile with enhanced synchronization"""
    st.markdown(f"### 👤 Profile: {employee_data['name']}")
    
    # Show sync status
    current_employee_id = get_current_employee_id()
    if current_employee_id == employee_id:
        st.info("🔄 This profile is synchronized with the Employee Portal")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Basic Information")
        
        # Editable fields
        name = st.text_input("Name", value=employee_data["name"], key=f"name_{employee_id}")
        
        current_role = st.selectbox(
            "Current Role", 
            options=list(role_requirements.keys()), 
            index=list(role_requirements.keys()).index(employee_data["current_role"]) 
            if employee_data["current_role"] in role_requirements else 0,
            key=f"role_{employee_id}"
        )
        
        experience_level = st.selectbox(
            "Experience Level",
            ["Entry Level", "Junior", "Mid-level", "Senior", "Expert"],
            index=["Entry Level", "Junior", "Mid-level", "Senior", "Expert"].index(
                employee_data.get("experience_level", "Mid-level")
            ),
            key=f"exp_{employee_id}"
        )
        
        department = st.text_input(
            "Department", 
            value=employee_data.get("department", ""), 
            key=f"dept_{employee_id}"
        )
    
    with col2:
        st.markdown("#### Skills & Proficiency")
        
        # Get all available skills from role requirements
        all_skills = set()
        for role_data in role_requirements.values():
            all_skills.update(role_data["required_skills"].keys())
            all_skills.update(role_data["preferred_skills"].keys())
        
        skills = st.multiselect(
            "Current Skills", 
            options=sorted(list(all_skills)), 
            default=list(employee_data["skill_proficiency"].keys()), # Use keys from skill_proficiency
            key=f"skills_{employee_id}"
        )
        
        # Skill proficiency levels
        proficiency_levels = ["Beginner", "Intermediate", "Advanced", "Expert"]
        skill_proficiency = {}
        if skills:
            st.markdown("**Skill Proficiency Levels:**")
            for skill in skills:
                current_proficiency = employee_data.get("skill_proficiency", {}).get(skill, "Beginner") # Default to Beginner
                
                # Ensure the current_proficiency is in the list before finding index
                if current_proficiency not in proficiency_levels:
                    current_proficiency = "Beginner" # Fallback if proficiency is invalid
                
                proficiency = st.selectbox(
                    f"Proficiency in {skill}",
                    proficiency_levels,
                    index=proficiency_levels.index(current_proficiency),
                    key=f"prof_{skill}_{employee_id}"
                )
                skill_proficiency[skill] = proficiency
    
    # Career goals and completed courses
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("#### Career Goals")
        career_goals = st.multiselect(
            "Career Aspirations", 
            options=list(role_requirements.keys()), 
            default=employee_data["career_goals"],
            key=f"goals_{employee_id}"
        )
    
    with col4:
        st.markdown("#### Completed Courses")
        all_courses = course_catalog["title"].tolist()
        completed_courses = st.multiselect(
            "Completed Courses", 
            options=all_courses,
            default=employee_data["completed_courses"],
            key=f"courses_{employee_id}"
        )
    
    # Enhanced update buttons with synchronization
    col_update, col_sync, col_reset = st.columns(3)
    
    with col_update:
        if st.button("✅ Update Profile", type="primary", key=f"update_{employee_id}"):
            updated_profile = {
                "name": name,
                "current_role": current_role,
                "skills": list(skill_proficiency.keys()), # Update skills list based on proficiency keys
                "skill_proficiency": skill_proficiency,
                "completed_courses": completed_courses,
                "career_goals": career_goals,
                "experience_level": experience_level,
                "department": department
            }
            
            # Use enhanced sync function
            if sync_employee_profile_changes(employee_id, updated_profile):
                st.success(f"✅ Profile updated and synchronized for {name}!")
                
                # If this employee's learning path exists, consider regenerating it
                if (employee_id in st.session_state.employee_database and 
                    st.session_state.employee_database[employee_id].get('assigned_learning_path')):
                    st.info("💡 Profile changes detected. Consider regenerating the learning path to reflect these updates.")
                
                st.rerun()
            else:
                st.error("Failed to update profile.")
    
    with col_sync:
        if st.button("🔄 Sync to Employee", key=f"sync_{employee_id}"):
            # Force sync this profile to the employee portal if they're the same person
            current_employee_id = get_current_employee_id()
            if current_employee_id == employee_id:
                updated_profile = {
                    "name": name,
                    "current_role": current_role,
                    "skills": list(skill_proficiency.keys()),
                    "skill_proficiency": skill_proficiency,
                    "completed_courses": completed_courses,
                    "career_goals": career_goals,
                    "experience_level": experience_level,
                    "department": department
                }
                
                if sync_employee_profile_changes(employee_id, updated_profile):
                    st.success("🔄 Profile synchronized with Employee Portal!")
                    st.rerun()
            else:
                st.warning("Can only sync profile for the currently selected employee.")
    
    with col_reset:
        if st.button("🔄 Reset Changes", key=f"reset_{employee_id}"):
            st.rerun()


def generate_learning_path_for_employee(employee_id, employee_data):
    """Generate learning path for selected employee"""
    st.markdown(f"### 🎯 Generate Learning Path for {employee_data['name']}")
    
    # Learning preferences for the employee
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Learning Constraints")
        
        time_available = st.number_input(
            "Time Available (weeks)", 
            min_value=1, 
            max_value=52, 
            value= 20,#st.session_state.learning_path.get("total_duration_weeks", 0),
            key=f"time_{employee_id}"
        )
        
        learning_style = st.selectbox(
            "Preferred Learning Style",
            ["Mixed", "Visual", "Hands-on", "Interactive", "Intensive"],
            key=f"style_{employee_id}"
        )
        
        difficulty_preference = st.selectbox(
            "Difficulty Preference",
            ["Progressive", "Beginner", "Intermediate", "Advanced"],
            key=f"difficulty_{employee_id}"
        )
    
    with col2:
        st.markdown("#### Focus Areas")
        urgency = st.selectbox(
            "Learning Urgency",
            ["Low", "Medium", "High", "Critical"],
            index=1,
            key=f"urgency_{employee_id}"
        )
        
        # Additional skills to focus on
        all_skills = set()
        for role_data in role_requirements.values():
            all_skills.update(role_data["required_skills"].keys())
            all_skills.update(role_data["preferred_skills"].keys())
        
        focus_skills = st.multiselect(
            "Additional Skills to Focus On",
            options=sorted(list(all_skills)),
            key=f"focus_{employee_id}"
        )
    
    # Generate button
    if st.button("🚀 Generate Learning Path", type="primary", key=f"generate_{employee_id}"):
        with st.spinner("Generating personalized learning path..."):
            # Create learning preferences object
            learning_preferences = LearningPreference(
                time_available_weeks=time_available,
                preferred_learning_style=learning_style,
                difficulty_preference=difficulty_preference,
                specific_skills_requested=focus_skills,
                learning_urgency=urgency
            )
            
            # Generate learning path
            learning_path = generate_enhanced_learning_path_with_sync(
                employee_data,
                learning_preferences
            )
            
            if learning_path:
                # Assign to employee
                assign_learning_path_to_employee(employee_id, learning_path)
                
                # Initialize progress for the new path
                st.session_state.learning_path_progress[employee_id] = {}
                for course in learning_path.get('learning_path', []):
                    course_id = course.get('id')
                    if course_id:
                        st.session_state.learning_path_progress[employee_id][course_id] = {
                            "status": "Not Started", 
                            "start_date": None, 
                            "completion_date": None
                        }
                for course in learning_path.get('udemy_courses', []):
                    course_id = course.get('id')
                    if course_id:
                        st.session_state.learning_path_progress[employee_id][course_id] = {
                            "status": "Not Started", 
                            "start_date": None, 
                            "completion_date": None
                        }

                st.success(f"✅ Learning path generated and assigned to {employee_data['name']}!")
                
                # Display summary
                st.markdown("#### 📊 Learning Path Summary")
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Total Duration", f"{learning_path.get('total_duration_weeks', 0)} weeks")
                with col_b:
                    st.metric("Courses", len(learning_path.get('learning_path', [])))
                with col_c:
                    st.metric("Skills Covered", len(learning_path.get('skill_gaps_addressed', [])))
                
                # Show brief course list
                st.markdown("**Recommended Courses:**")
                for i, course in enumerate(learning_path.get('learning_path', []), 1):
                    priority_emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(
                        course.get('priority', 'Medium'), "⚪"
                    )
                    st.markdown(f"{i}. {course.get('title')} {priority_emoji} - {course.get('duration')}")
                
                st.info("💡 The employee can now view and interact with this learning path in the Employee Portal.")

def display_assigned_learning_path(employee_id, employee_data):
    """Display the currently assigned learning path"""
    st.markdown(f"### 📚 Current Learning Path for {employee_data['name']}")
    
    assigned_path = employee_data.get('assigned_learning_path')
    if not assigned_path:
        st.info("No learning path assigned yet. Generate one in the 'Generate Learning Path' tab.")
        return
    
    # Path overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Duration", f"{assigned_path.get('total_duration_weeks', 0)} weeks")
    with col2:
        st.metric("Courses", len(assigned_path.get('learning_path', [])))
    with col3:
        st.metric("Skills", len(assigned_path.get('skill_gaps_addressed', [])))
    with col4:
        udemy_count = len(assigned_path.get('udemy_courses', []))
        st.metric("Udemy Courses", udemy_count)
    
    # Strategy explanation
    if assigned_path.get('explanation'):
        st.info(f"**Strategy:** {assigned_path['explanation']}")
    
    # Course details
    st.markdown("#### 📋 Course Details")
    
    for i, course in enumerate(assigned_path.get('learning_path', []), 1):
        with st.expander(f"{i}. {course.get('title')} - {course.get('priority', 'Medium')} Priority"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**Type:** {course.get('type')}")
                st.markdown(f"**Duration:** {course.get('duration')}")
                st.markdown(f"**Skills:** {', '.join(course.get('skills_gained', []))}")
            with col_b:
                st.markdown(f"**Priority:** {course.get('priority')}")
                st.markdown(f"**Reason:** {course.get('reason', 'N/A')}")
    
    # Udemy courses
    udemy_courses = assigned_path.get('udemy_courses', [])
    if udemy_courses:
        st.markdown("#### 🌟 Udemy Course Recommendations")
        for i, course in enumerate(udemy_courses, 1):
            with st.expander(f"{i}. {course.get('title')} - ⭐{course.get('rating', 4.0)}"):
                col_x, col_y = st.columns(2)
                with col_x:
                    st.markdown(f"**Price:** {course.get('price')}")
                    st.markdown(f"**Duration:** {course.get('duration')}")
                    st.markdown(f"**Level:** {course.get('level')}")
                with col_y:
                    st.markdown(f"**Rating:** ⭐{course.get('rating', 4.0)}")
                    st.link_button("View on Udemy", course.get('url', '#'))
                
                st.markdown(f"**Description:** {course.get('description', 'N/A')}")
    
    # Action buttons
    col_remove, col_regenerate = st.columns(2)
    
    with col_remove:
        if st.button("🗑️ Remove Learning Path", key=f"remove_{employee_id}"):
            st.session_state.employee_database[employee_id]['assigned_learning_path'] = None
            if employee_id in st.session_state.learning_path_progress:
                del st.session_state.learning_path_progress[employee_id]
            st.success("Learning path removed successfully!")
            st.rerun()
    
    with col_regenerate:
        if st.button("🔄 Regenerate Path", key=f"regenerate_{employee_id}"):
            st.info("Use the 'Generate Learning Path' tab to create a new learning path.")

# employee sync
def sync_employee_learning_path(employee_id, learning_path):
    """Synchronize learning path between employee and manager portals"""
    if employee_id and employee_id in st.session_state.employee_database:
        # Update the employee database with the new learning path
        st.session_state.employee_database[employee_id]['assigned_learning_path'] = learning_path
        
        # Also update the current session learning path
        # Only update if the current employee profile matches the one being synced
        if st.session_state.employee_profile.get('employee_id') == employee_id:
            st.session_state.learning_path = learning_path
        
        return True
    return False

def get_current_employee_id():
    """Get the current employee ID based on the employee profile"""
    if 'employee_profile' in st.session_state:
        return st.session_state.employee_profile.get('employee_id')
    # Fallback for manager/admin portal if employee_profile isn't set for the session
    return st.session_state.get('selected_employee_id')


# --- New Admin/HR Portal Functions ---
def admin_hr_portal_page():
    with st.sidebar:
        # Save/Load buttons
        st.markdown("### 💾 Data Management")
        col_save, col_load = st.columns(2)
        with col_save:
            if st.button("💾 Save All Paths", help="Save all employee learning paths and progress"):
                save_all_learning_paths()
        with col_load:
            if st.button("📂 Load All Paths", help="Load all employee learning paths and progress"):
                load_all_learning_paths()
    """Admin/HR Portal page to manage all employees and generate default learning paths."""
    st.title("🏢 Admin/HR Portal - Employee Learning Overview")
    st.markdown("*Manage all employee profiles and assign default learning paths.*")

    # Display all employees
    st.markdown("### 👥 All Employees Overview")
    employees_df = pd.DataFrame(st.session_state.employee_database.values())
    
    # Select relevant columns for display
    display_cols = ['employee_id', 'name', 'current_role', 'department', 'manager_id', 'experience_level']
    if not employees_df.empty:
        st.dataframe(employees_df[display_cols].set_index('employee_id'), use_container_width=True)
    else:
        st.info("No employee data available.")

    st.markdown("---")
    st.markdown("### 🚀 Generate Default Learning Paths for Selected Employees")

    # Individual employee selection for default path generation
    all_employees = st.session_state.employee_database
    if not all_employees:
        st.info("No employees to generate paths for.")
        return

    employee_options_for_multiselect = {f"{emp_data['name']} ({emp_id})": emp_id 
                                       for emp_id, emp_data in all_employees.items()}
    
    selected_employee_ids_for_default_lp = st.multiselect(
        "Select employees for default learning path generation:",
        options=list(employee_options_for_multiselect.keys()),
        default=[],
        format_func=lambda x: x.split('(')[0].strip(), # Display only name in selected tags
        key="admin_default_lp_employee_selector"
    )

    # Convert display names back to IDs
    selected_ids = [employee_options_for_multiselect[display_name] for display_name in selected_employee_ids_for_default_lp]

    if st.button(f"✨ Generate Default Learning Paths for {len(selected_ids)} Selected Employees", type="primary", key="generate_selected_default_lp"):
        if not selected_ids:
            st.warning("Please select at least one employee to generate a default learning path.")
        else:
            with st.spinner(f"Generating default learning paths for {len(selected_ids)} employees... This may take a moment."):
                generated_count = 0
                for emp_id in selected_ids:
                    emp_data = st.session_state.employee_database[emp_id]
                    # Create a default learning preference for the general path
                    default_learning_preferences = LearningPreference(
                        time_available_weeks=20,  # 12-week default
                        preferred_learning_style="Mixed",
                        difficulty_preference="Progressive",
                        specific_skills_requested=["Data Analysis", "Project Management", "Communication"], # Generic skills
                        learning_urgency="Medium"
                    )
                    
                    # Generate a learning path based on the employee's current role and the default focus
                    # Use a copy of employee data to avoid modifying it during generation
                    employee_data_copy = emp_data.copy()
                    # For default paths, focus on current role's requirements
                    #employee_data_copy["career_goals"] = [employee_data_copy["current_role"]] 
                    
                    default_path = generate_enhanced_learning_path(
                        employee_data_copy,
                        default_learning_preferences,
                        specific_requirements={"mentioned_skills": default_learning_preferences.specific_skills_requested}
                    )
                    
                    if default_path:
                        assign_learning_path_to_employee(emp_id, default_path)
                        # Initialize progress for the new path
                        st.session_state.learning_path_progress[emp_id] = {}
                        for course in default_path.get('learning_path', []):
                            course_id = course.get('id')
                            if course_id:
                                st.session_state.learning_path_progress[emp_id][course_id] = {
                                    "status": "Not Started", 
                                    "start_date": None, 
                                    "completion_date": None
                                }
                        for course in default_path.get('udemy_courses', []):
                            course_id = course.get('id')
                            if course_id:
                                st.session_state.learning_path_progress[emp_id][course_id] = {
                                    "status": "Not Started", 
                                    "start_date": None, 
                                    "completion_date": None
                                }
                        generated_count += 1
                
                st.success(f"✅ Successfully generated default learning paths for {generated_count} employees!")
                st.rerun()
    
    st.markdown("---")
    st.markdown("### 🔍 Manage Individual Employee Learning Paths & Skill Gaps")

    # Individual employee selection (similar to manager portal)
    all_employees_for_individual = st.session_state.employee_database
    if not all_employees_for_individual:
        st.info("No employees to manage individually.")
        return

    employee_options_individual = {f"{emp_data['name']} ({emp_id})": emp_id 
                                  for emp_id, emp_data in all_employees_for_individual.items()}
    
    selected_employee_display_individual = st.selectbox(
        "Choose an employee to manage their learning path and view skill gaps:",
        options=list(employee_options_individual.keys()),
        key="admin_employee_selector_individual"
    )
    
    if selected_employee_display_individual:
        selected_employee_id_individual = employee_options_individual[selected_employee_display_individual]
        st.session_state.selected_employee_id = selected_employee_id_individual # Set for reuse in other functions
        
        employee_data_individual = st.session_state.employee_database[selected_employee_id_individual]
        
        # Display employee information in tabs (reusing manager portal functions)
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Employee Profile", "📊 Skill Gap Analysis", "🎯 Generate Learning Path", "📚 Assigned Learning Path"])
        
        with tab1:
            display_and_edit_employee_profile(selected_employee_id_individual, employee_data_individual)
        
        with tab2:
            display_skill_gap_analysis(selected_employee_id_individual, employee_data_individual)

        with tab3:
            generate_learning_path_for_employee(selected_employee_id_individual, employee_data_individual)
        
        with tab4:
            display_assigned_learning_path(selected_employee_id_individual, employee_data_individual)

def display_skill_gap_analysis(employee_id, employee_data):
    """Display skill gap analysis for a selected employee in a table."""
    st.markdown(f"### 📊 Skill Gap Analysis for {employee_data['name']}")

    current_role_reqs = role_requirements.get(employee_data['current_role'], {})
    career_goal_reqs_list = []
    for goal in employee_data['career_goals']:
        career_goal_reqs_list.append(role_requirements.get(goal, {}))

    skill_gaps_data = calculate_skill_gaps(
        employee_data,
        current_role_reqs,
        career_goal_reqs_list
    )

    if skill_gaps_data:
        st.markdown("#### Identified Skill Gaps for Career Progression")
        gap_df = pd.DataFrame(skill_gaps_data)
        st.dataframe(gap_df, use_container_width=True)
    else:
        st.info(f"No significant skill gaps identified for {employee_data['name']} based on their current role and career goals, or they meet all current requirements.")

    st.markdown("---")
    st.markdown("#### Current Skill Proficiency")
    if employee_data.get('skill_proficiency'):
        proficiency_df = pd.DataFrame([
            {"Skill": skill, "Proficiency": level}
            for skill, level in employee_data['skill_proficiency'].items()
        ])
        st.dataframe(proficiency_df, use_container_width=True)
    else:
        st.info(f"{employee_data['name']} has no recorded skill proficiencies. Please update their profile.")

# --- New Dashboard Page ---
# def dashboard_page():
#     st.title("📈 Learning Path Dashboard")
#     st.markdown("*Overview of all assigned learning paths and employee progress.*")

#     employees_with_paths = {emp_id: emp_data for emp_id, emp_data in st.session_state.employee_database.items()
#                             if emp_data.get('assigned_learning_path')}

#     if not employees_with_paths:
#         st.info("No learning paths have been assigned to employees yet. Assign paths from the Manager or Admin portals.")
#         return

#     # Calculate overall summary metrics
#     total_employees = len(employees_with_paths)
#     total_courses_assigned = 0
#     total_courses_completed = 0
#     employees_with_overdue = 0
#     employees_on_track = 0
#     employees_completed = 0
    
#     # Detailed metrics for summary
#     summary_data = {}
    
#     for emp_id, emp_data in employees_with_paths.items():
#         assigned_path = emp_data['assigned_learning_path']
#         progress_data = st.session_state.learning_path_progress.get(emp_id, {})
        
#         total_courses = len(assigned_path.get('learning_path', [])) + len(assigned_path.get('udemy_courses', []))
#         completed_courses_count = sum(1 for course_id, status_info in progress_data.items()
#                                       if status_info.get('status') == 'Completed')
        
#         total_courses_assigned += total_courses
#         total_courses_completed += completed_courses_count
        
#         # Check for overdue courses
#         overdue_courses = []
#         path_start_date = assigned_path.get('start_date', datetime.now().isoformat())
#         if isinstance(path_start_date, str):
#             path_start_date = datetime.fromisoformat(path_start_date)
            
#         all_courses_in_path = assigned_path.get('learning_path', []) + assigned_path.get('udemy_courses', [])
        
#         for course in all_courses_in_path:
#             course_id = course.get('id')
#             if not course_id:
#                 course_id = f"generated_{str(uuid.uuid4())}"
#                 course['id'] = course_id
            
#             status_info = progress_data.get(course_id, {"status": "Not Started", "start_date": None, "completion_date": None})
            
#             if status_info['status'] != "Completed":
#                 course_duration_weeks = course.get('duration_weeks', 0)
#                 expected_completion_date = None
                
#                 if status_info.get('start_date'):
#                     course_start = datetime.fromisoformat(status_info['start_date'])
#                     expected_completion_date = course_start + timedelta(weeks=course_duration_weeks)
#                 elif path_start_date:
#                     expected_completion_date = path_start_date + timedelta(weeks=course_duration_weeks)
                
#                 if expected_completion_date and datetime.now() > expected_completion_date:
#                     overdue_courses.append(course)
        
#         # Categorize employees
#         progress_percentage = (completed_courses_count / total_courses) * 100 if total_courses > 0 else 0
        
#         summary_data[emp_id] = {
#             'name': emp_data['name'],
#             'role': emp_data['current_role'],
#             'total_courses': total_courses,
#             'completed_courses': completed_courses_count,
#             'progress_percentage': progress_percentage,
#             'overdue_count': len(overdue_courses),
#             'has_overdue': len(overdue_courses) > 0,
#             'total_duration': assigned_path.get('total_duration_weeks', 0)
#         }
        
#         if progress_percentage == 100:
#             employees_completed += 1
#         elif len(overdue_courses) > 0:
#             employees_with_overdue += 1
#         else:
#             employees_on_track += 1

#     # Display Overall Summary Section
#     st.markdown("## 📊 Overall Summary")
    
#     col1, col2, col3, col4, col5 = st.columns(5)
#     with col1:
#         st.metric("Total Employees", total_employees, help="Employees with assigned learning paths")
#     with col2:
#         st.metric("Total Courses", f"{total_courses_completed}/{total_courses_assigned}", 
#                  help="Completed courses out of total assigned")
#     with col3:
#         overall_completion = (total_courses_completed / total_courses_assigned) * 100 if total_courses_assigned > 0 else 0
#         st.metric("Overall Completion", f"{overall_completion:.1f}%")
#     with col4:
#         st.metric("🚨 With Overdue", employees_with_overdue, 
#                  delta=f"-{employees_with_overdue}" if employees_with_overdue > 0 else None,
#                  delta_color="inverse")
#     with col5:
#         st.metric("✅ Completed", employees_completed, 
#                  delta=f"+{employees_completed}" if employees_completed > 0 else None)

#     # Status breakdown chart
#     col1, col2 = st.columns(2)
#     with col1:
#         # Employee status distribution
#         status_data = {
#             'Status': ['Completed', 'On Track', 'With Overdue'],
#             'Count': [employees_completed, employees_on_track, employees_with_overdue]
#         }
        
#         if any(count > 0 for count in status_data['Count']):
#             fig_status = px.pie(status_data, values='Count', names='Status', 
#                               title="Employee Status Distribution",
#                               color_discrete_map={
#                                   'Completed': '#28a745',
#                                   'On Track': '#17a2b8', 
#                                   'With Overdue': '#dc3545'
#                               })
#             st.plotly_chart(fig_status, use_container_width=True)
    
#     with col2:
#         # Progress distribution
#         progress_ranges = {'0-25%': 0, '26-50%': 0, '51-75%': 0, '76-99%': 0, '100%': 0}
#         for emp_id, data in summary_data.items():
#             progress = data['progress_percentage']
#             if progress == 100:
#                 progress_ranges['100%'] += 1
#             elif progress > 75:
#                 progress_ranges['76-99%'] += 1
#             elif progress > 50:
#                 progress_ranges['51-75%'] += 1
#             elif progress > 25:
#                 progress_ranges['26-50%'] += 1
#             else:
#                 progress_ranges['0-25%'] += 1
        
#         progress_data = {
#             'Range': list(progress_ranges.keys()),
#             'Count': list(progress_ranges.values())
#         }
        
#         if any(count > 0 for count in progress_data['Count']):
#             fig_progress = px.bar(progress_data, x='Range', y='Count',
#                                 title="Progress Distribution",
#                                 color='Count',
#                                 color_continuous_scale='viridis')
#             st.plotly_chart(fig_progress, use_container_width=True)

#     st.markdown("---")

#     # Filter/Search and Employee Selection
#     st.markdown("## 🔍 Employee Details")
    
#     col1, col2 = st.columns([2, 1])
#     with col1:
#         search_term = st.text_input("🔍 Search Employee by Name or ID", key="dashboard_search")
#     with col2:
#         # Filter options
#         filter_option = st.selectbox("Filter by Status", 
#                                    ["All", "With Overdue", "On Track", "Completed"],
#                                    key="status_filter")
    
#     # Apply filters
#     filtered_employees = {}
#     for emp_id, emp_data in employees_with_paths.items():
#         # Apply search filter
#         if search_term and not (search_term.lower() in emp_data['name'].lower() or search_term.lower() in emp_id.lower()):
#             continue
            
#         # Apply status filter
#         emp_summary = summary_data[emp_id]
#         if filter_option == "With Overdue" and not emp_summary['has_overdue']:
#             continue
#         elif filter_option == "On Track" and (emp_summary['has_overdue'] or emp_summary['progress_percentage'] == 100):
#             continue
#         elif filter_option == "Completed" and emp_summary['progress_percentage'] != 100:
#             continue
            
#         filtered_employees[emp_id] = emp_data

#     if not filtered_employees:
#         st.warning("No employees found matching your search criteria and filters.")
#         return

#     # Employee selection dropdown
#     employee_options = ["View All"] + [f"{summary_data[emp_id]['name']} ({emp_id}) - {summary_data[emp_id]['progress_percentage']:.1f}%" 
#                                       for emp_id in filtered_employees.keys()]
    
#     selected_employee = st.selectbox("Select Employee to View Details", employee_options, key="employee_selector")

#     # Show selected employee(s)
#     if selected_employee == "View All":
#         # Show summary table for all filtered employees
#         st.markdown("### 📋 Employee Summary Table")
        
#         table_data = []
#         for emp_id in filtered_employees.keys():
#             data = summary_data[emp_id]
#             status_emoji = "🚨" if data['has_overdue'] else ("✅" if data['progress_percentage'] == 100 else "⏳")
#             table_data.append({
#                 'Status': status_emoji,
#                 'Employee': f"{data['name']} ({emp_id})",
#                 'Role': data['role'],
#                 'Progress': f"{data['progress_percentage']:.1f}%",
#                 'Courses': f"{data['completed_courses']}/{data['total_courses']}",
#                 'Overdue': data['overdue_count'],
#                 'Duration': f"{data['total_duration']} weeks"
#             })
        
#         df = pd.DataFrame(table_data)
#         st.dataframe(df, use_container_width=True, hide_index=True)
        
#         # Quick actions for employees with overdue courses
#         overdue_employees = [emp_id for emp_id in filtered_employees.keys() if summary_data[emp_id]['has_overdue']]
#         if overdue_employees:
#             st.markdown("### ⚡ Quick Actions for Overdue Employees")
#             cols = st.columns(min(3, len(overdue_employees)))
#             for i, emp_id in enumerate(overdue_employees[:3]):  # Show max 3 in one row
#                 with cols[i]:
#                     emp_name = summary_data[emp_id]['name']
#                     if st.button(f"🔄 Regenerate Path\n{emp_name}", key=f"quick_regen_{emp_id}"):
#                         # Trigger regeneration (same logic as below)
#                         st.session_state['selected_employee_for_regen'] = emp_id
#                         st.rerun()
#     else:
#         # Extract employee ID from selection
#         selected_emp_id = selected_employee.split('(')[1].split(')')[0]
#         emp_data = filtered_employees[selected_emp_id]
        
#         # Show detailed view for selected employee
#         show_detailed_employee_view(selected_emp_id, emp_data, summary_data[selected_emp_id])

# def show_detailed_employee_view(emp_id, emp_data, emp_summary):
#     """Display detailed view for a single employee"""
#     assigned_path = emp_data['assigned_learning_path']
#     progress_data = st.session_state.learning_path_progress.get(emp_id, {})
    
#     st.markdown(f"### 🧑‍💻 {emp_data['name']} ({emp_id}) - {emp_data['current_role']}")
    
#     # Employee metrics
#     col1, col2, col3, col4 = st.columns(4)
#     with col1:
#         st.metric("Total Courses", emp_summary['total_courses'])
#     with col2:
#         st.metric("Completed Courses", emp_summary['completed_courses'])
#     with col3:
#         st.metric("Progress", f"{emp_summary['progress_percentage']:.1f}%")
#     with col4:
#         st.metric("Total Duration", f"{emp_summary['total_duration']} weeks")

#     # Progress bar
#     progress_bar = st.progress(emp_summary['progress_percentage'] / 100)
    
#     if emp_summary['has_overdue']:
#         st.error(f"🚨 **Alert:** {emp_summary['overdue_count']} courses are overdue!")

#     st.markdown("#### 📚 Course Progress Details:")
    
#     # Course details
#     overdue_courses = []
#     path_start_date = assigned_path.get('start_date', datetime.now().isoformat())
#     if isinstance(path_start_date, str):
#         path_start_date = datetime.fromisoformat(path_start_date)

#     all_courses_in_path = assigned_path.get('learning_path', []) + assigned_path.get('udemy_courses', [])
    
#     for course in all_courses_in_path:
#         course_id = course.get('id')
#         if not course_id:
#             course_id = f"generated_{str(uuid.uuid4())}"
#             course['id'] = course_id
        
#         status_info = progress_data.get(course_id, {"status": "Not Started", "start_date": None, "completion_date": None})
        
#         display_status = status_info['status']
#         status_emoji = "⚪"
#         if display_status == "Completed":
#             status_emoji = "✅"
#         elif display_status == "In Progress":
#             status_emoji = "⏳"

#         course_duration_weeks = course.get('duration_weeks', 0)
        
#         # Calculate expected completion date
#         expected_completion_date = None
#         completion_info = ""
        
#         if status_info.get('start_date'):
#             course_start = datetime.fromisoformat(status_info['start_date'])
#             expected_completion_date = course_start + timedelta(weeks=course_duration_weeks)
#         elif path_start_date:
#             expected_completion_date = path_start_date + timedelta(weeks=course_duration_weeks)

#         is_overdue = False
#         if display_status != "Completed" and expected_completion_date and datetime.now() > expected_completion_date:
#             is_overdue = True
#             overdue_courses.append(course)
#             status_emoji = "🚨"
#             completion_info = f"<span style='color: red;'>**OVERDUE!** Expected by: {expected_completion_date.strftime('%Y-%m-%d')}</span>"
#         elif expected_completion_date:
#             completion_info = f"Expected completion: {expected_completion_date.strftime('%Y-%m-%d')}"
        
#         # Display course info in an expandable section
#         with st.expander(f"{status_emoji} **{course.get('title')}** ({course.get('duration')}) - {display_status}"):
#             if completion_info:
#                 st.markdown(completion_info, unsafe_allow_html=True)
            
#             if course.get('skills_gained'):
#                 st.markdown(f"**Skills:** {', '.join(course['skills_gained'])}")
            
#             if status_info.get('completion_date'):
#                 completion_date = datetime.fromisoformat(status_info['completion_date'])
#                 st.markdown(f"**Completed on:** {completion_date.strftime('%Y-%m-%d')}")

#     # Regeneration section
#     if overdue_courses:
#         st.markdown("---")
#         st.warning(f"🚨 **Alert for {emp_data['name']}:** {len(overdue_courses)} courses are overdue!")
        
#         col1, col2 = st.columns([1, 2])
#         with col1:
#             if st.button(f"🔄 Regenerate Shorter Path", key=f"regenerate_shorter_{emp_id}"):
#                 regenerate_learning_path(emp_id, emp_data, overdue_courses, all_courses_in_path, progress_data, assigned_path)

# def regenerate_learning_path(emp_id, emp_data, overdue_courses, all_courses_in_path, progress_data, assigned_path):
#     """Handle learning path regeneration"""
#     with st.spinner(f"Regenerating shorter path for {emp_data['name']}..."):
#         # Collect skills from overdue courses and remaining path
#         skills_to_cover = set()
#         for oc in overdue_courses:
#             skills_to_cover.update(oc.get('skills_gained', []))
#             if oc.get('title'):
#                 skills_to_cover.add(oc['title'].split(' ')[0])
        
#         # Also include skills from remaining uncompleted courses
#         for course in all_courses_in_path:
#             course_id = course.get('id')
#             status_info = progress_data.get(course_id, {})
#             if status_info.get('status') != 'Completed':
#                 skills_to_cover.update(course.get('skills_gained', []))
#                 if course.get('title'):
#                     skills_to_cover.add(course['title'].split(' ')[0])

#         # Create a learning preference object for shorter duration
#         original_duration = assigned_path.get('total_duration_weeks', 20)
#         new_time_available = max(4, original_duration - 4)

#         shorter_preferences = LearningPreference(
#             time_available_weeks=new_time_available,
#             preferred_learning_style=st.session_state.learning_preferences.preferred_learning_style,
#             difficulty_preference=st.session_state.learning_preferences.difficulty_preference,
#             specific_skills_requested=list(skills_to_cover),
#             learning_urgency="High"
#         )

#         new_learning_path = generate_enhanced_learning_path_with_sync(
#             emp_data,
#             shorter_preferences,
#             specific_requirements={"shorten_duration": True, "skills_to_focus": list(skills_to_cover)}
#         )
        
#         if new_learning_path:
#             assign_learning_path_to_employee(emp_id, new_learning_path)
#             # Re-initialize progress for the new path
#             st.session_state.learning_path_progress[emp_id] = {}
#             current_time = datetime.now().isoformat()
            
#             for course in new_learning_path.get('learning_path', []):
#                 course_id = course.get('id')
#                 if course_id:
#                     st.session_state.learning_path_progress[emp_id][course_id] = {
#                         "status": "Not Started", 
#                         "start_date": current_time,
#                         "completion_date": None
#                     }
#             for course in new_learning_path.get('udemy_courses', []):
#                 course_id = course.get('id')
#                 if course_id:
#                     st.session_state.learning_path_progress[emp_id][course_id] = {
#                         "status": "Not Started", 
#                         "start_date": current_time,
#                         "completion_date": None
#                     }
#             st.success(f"✅ Shorter learning path generated and assigned to {emp_data['name']}!")
#             st.rerun()
#         else:
#             st.error(f"Failed to regenerate shorter learning path for {emp_data['name']}.")

def dashboard_page():
    st.title("📈 Learning Path Dashboard")
    st.markdown("*Comprehensive overview of learning paths and employee progress.*")

    employees_with_paths = {emp_id: emp_data for emp_id, emp_data in st.session_state.employee_database.items()
                            if emp_data.get('assigned_learning_path')}

    if not employees_with_paths:
        st.info("No learning paths have been assigned to employees yet. Assign paths from the Manager or Admin portals.")
        return

    # Overall Summary Section
    st.markdown("## 📊 Overall Summary")
    
    total_employees = len(employees_with_paths)
    total_overdue_employees = 0
    total_completed_employees = 0
    total_in_progress_employees = 0
    total_not_started_employees = 0
    total_courses_across_all = 0
    total_completed_courses_across_all = 0
    
    # Calculate summary statistics
    employees_summary = {}
    for emp_id, emp_data in employees_with_paths.items():
        assigned_path = emp_data['assigned_learning_path']
        progress_data = st.session_state.learning_path_progress.get(emp_id, {})
        
        total_courses = len(assigned_path.get('learning_path', [])) + len(assigned_path.get('udemy_courses', []))
        completed_courses_count = sum(1 for course_id, status_info in progress_data.items()
                                      if status_info.get('status') == 'Completed')
        
        total_courses_across_all += total_courses
        total_completed_courses_across_all += completed_courses_count
        
        # Check for overdue courses
        path_start_date = assigned_path.get('start_date', datetime.now().isoformat())
        if isinstance(path_start_date, str):
            path_start_date = datetime.fromisoformat(path_start_date)
        
        all_courses_in_path = assigned_path.get('learning_path', []) + assigned_path.get('udemy_courses', [])
        overdue_courses = []
        
        for course in all_courses_in_path:
            course_id = course.get('id')
            if not course_id:
                course_id = f"generated_{str(uuid.uuid4())}"
                course['id'] = course_id
            
            status_info = progress_data.get(course_id, {"status": "Not Started", "start_date": None, "completion_date": None})
            course_duration_weeks = course.get('duration_weeks', 2)  # Default to 2 weeks if not specified
            
            expected_completion_date = None
            # Use individual course start date if available, otherwise use path start date
            if status_info.get('start_date') and status_info['start_date'] is not None:
                course_start = datetime.fromisoformat(status_info['start_date'])
                expected_completion_date = course_start + timedelta(weeks=course_duration_weeks)
            elif path_start_date:
                # For courses without individual start dates, calculate based on path start date
                # Assume courses start sequentially or use path start date as fallback
                expected_completion_date = path_start_date + timedelta(weeks=course_duration_weeks)
            
            # A course is overdue if it's not completed and past expected completion date
            if (status_info['status'] != "Completed" and 
                expected_completion_date and 
                datetime.now() > expected_completion_date):
                overdue_courses.append(course)
        
        # Determine employee status
        if total_courses == completed_courses_count and total_courses > 0:
            employee_status = "Completed"
            total_completed_employees += 1
        elif completed_courses_count > 0:
            employee_status = "In Progress"
            total_in_progress_employees += 1
        else:
            employee_status = "Not Started"
            total_not_started_employees += 1
        
        if overdue_courses:
            total_overdue_employees += 1
        
        progress_percentage = (completed_courses_count / total_courses) * 100 if total_courses > 0 else 0
        
        employees_summary[emp_id] = {
            'name': emp_data['name'],
            'role': emp_data['current_role'],
            'total_courses': total_courses,
            'completed_courses': completed_courses_count,
            'progress_percentage': progress_percentage,
            'status': employee_status,
            'overdue_courses': len(overdue_courses),
            'duration_weeks': assigned_path.get('total_duration_weeks', 0),
            'has_overdue': len(overdue_courses) > 0
        }
    
    # Display summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Employees", total_employees)
    with col2:
        st.metric("🚨 Overdue", total_overdue_employees, delta_color="inverse")
    with col3:
        st.metric("✅ Completed", total_completed_employees)
    with col4:
        st.metric("⏳ In Progress", total_in_progress_employees)
    with col5:
        st.metric("⚪ Not Started", total_not_started_employees)
    
    # Overall progress bar
    overall_progress = (total_completed_courses_across_all / total_courses_across_all) * 100 if total_courses_across_all > 0 else 0
    st.markdown(f"### Overall Progress: {overall_progress:.1f}%")
    st.progress(overall_progress / 100)
    
    # Quick stats table
    st.markdown("### 📋 Quick Overview")
    overview_data = []
    for emp_id, summary in employees_summary.items():
        status_emoji = "✅" if summary['status'] == "Completed" else "⏳" if summary['status'] == "In Progress" else "⚪"
        if summary['has_overdue']:
            status_emoji = "🚨"
        
        overview_data.append({
            "Employee": f"{status_emoji} {summary['name']}",
            "Role": summary['role'],
            "Progress": f"{summary['progress_percentage']:.1f}%",
            "Courses": f"{summary['completed_courses']}/{summary['total_courses']}",
            "Status": summary['status'],
            "Overdue": summary['overdue_courses'] if summary['overdue_courses'] > 0 else "-"
        })
    
    st.dataframe(overview_data, use_container_width=True)
    
    # Alert section for overdue employees
    if total_overdue_employees > 0:
        st.markdown("### 🚨 Attention Required")
        overdue_employees = [summary['name'] for summary in employees_summary.values() if summary['has_overdue']]
        st.warning(f"**{total_overdue_employees} employees have overdue courses:** {', '.join(overdue_employees)}")
    
    st.markdown("---")
    
    # Employee Selection Section
    st.markdown("## 👤 Employee Details")
    
    # Create employee options for selectbox
    employee_options = ["Select an employee..."] + [f"{emp_data['name']} ({emp_id}) - {emp_data['current_role']}" 
                                                    for emp_id, emp_data in employees_with_paths.items()]
    
    selected_employee_option = st.selectbox(
        "Select Employee to View Details:",
        options=employee_options,
        key="employee_detail_select"
    )
    
    if selected_employee_option != "Select an employee...":
        # Extract employee ID from selection
        selected_emp_id = selected_employee_option.split('(')[1].split(')')[0]
        emp_data = employees_with_paths[selected_emp_id]
        
        # Search functionality for the selected view
        search_term = st.text_input("Search within this employee's courses", key="course_search")
        
        # Display detailed view for selected employee
        assigned_path = emp_data['assigned_learning_path']
        progress_data = st.session_state.learning_path_progress.get(selected_emp_id, {})

        total_courses = len(assigned_path.get('learning_path', [])) + len(assigned_path.get('udemy_courses', []))
        completed_courses_count = sum(1 for course_id, status_info in progress_data.items()
                                      if status_info.get('status') == 'Completed')

        st.markdown(f"### 🧑‍💻 {emp_data['name']} ({selected_emp_id}) - {emp_data['current_role']}")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Courses", total_courses)
        with col2:
            st.metric("Completed Courses", completed_courses_count)
        with col3:
            if total_courses > 0:
                progress_percentage = (completed_courses_count / total_courses) * 100
                st.metric("Progress", f"{progress_percentage:.1f}%")
            else:
                st.metric("Progress", "0%")
        with col4:
            st.metric("Total Duration", f"{assigned_path.get('total_duration_weeks', 0)} weeks")

        # Progress visualization
        if total_courses > 0:
            st.progress(progress_percentage / 100)

        st.markdown("#### 📚 Course Progress Details:")
        overdue_courses = []
        path_start_date = assigned_path.get('start_date', datetime.now().isoformat())
        if isinstance(path_start_date, str):
            path_start_date = datetime.fromisoformat(path_start_date)

        all_courses_in_path = assigned_path.get('learning_path', []) + assigned_path.get('udemy_courses', [])
        
        # Filter courses based on search term
        filtered_courses = []
        for course in all_courses_in_path:
            if not search_term or search_term.lower() in course.get('title', '').lower():
                filtered_courses.append(course)
        
        if search_term and not filtered_courses:
            st.info("No courses found matching your search criteria.")
        elif filtered_courses:
            # Tabs for different course statuses
            tab1, tab2, tab3, tab4 = st.tabs(["📋 All Courses", "✅ Completed", "⏳ In Progress", "🚨 Overdue"])
            
            with tab1:
                display_courses(filtered_courses, progress_data, path_start_date, "all")
            
            with tab2:
                completed_courses = [c for c in filtered_courses if progress_data.get(c.get('id'), {}).get('status') == 'Completed']
                if completed_courses:
                    display_courses(completed_courses, progress_data, path_start_date, "completed")
                else:
                    st.info("No completed courses yet.")
            
            with tab3:
                in_progress_courses = [c for c in filtered_courses if progress_data.get(c.get('id'), {}).get('status') == 'In Progress']
                if in_progress_courses:
                    display_courses(in_progress_courses, progress_data, path_start_date, "in_progress")
                else:
                    st.info("No courses currently in progress.")
            
            with tab4:
                # Calculate overdue courses for this view
                overdue_courses_filtered = []
                for course in filtered_courses:
                    course_id = course.get('id')
                    if not course_id:
                        course_id = f"generated_{str(uuid.uuid4())}"
                        course['id'] = course_id
                    
                    status_info = progress_data.get(course_id, {"status": "Not Started", "start_date": None, "completion_date": None})
                    course_duration_weeks = course.get('duration_weeks', 2)  # Default to 2 weeks
                    
                    expected_completion_date = None
                    if status_info.get('start_date') and status_info['start_date'] is not None:
                        course_start = datetime.fromisoformat(status_info['start_date'])
                        expected_completion_date = course_start + timedelta(weeks=course_duration_weeks)
                    elif path_start_date:
                        expected_completion_date = path_start_date + timedelta(weeks=course_duration_weeks)
                    
                    if (status_info['status'] != "Completed" and 
                        expected_completion_date and 
                        datetime.now() > expected_completion_date):
                        overdue_courses_filtered.append(course)
                        overdue_courses.append(course)
                
                if overdue_courses_filtered:
                    st.warning(f"🚨 **{len(overdue_courses_filtered)} courses are overdue for {emp_data['name']}!**")
                    display_courses(overdue_courses_filtered, progress_data, path_start_date, "overdue")
                else:
                    st.success("✅ No overdue courses!")

        # Regenerate shorter path functionality (kept from original)
        if overdue_courses:
            st.markdown("---")
            st.markdown("#### 🔄 Course Management")
            if st.button(f"🔄 Regenerate Shorter Path for {emp_data['name']}", key=f"regenerate_shorter_{selected_emp_id}"):
                with st.spinner(f"Regenerating shorter path for {emp_data['name']}..."):
                    # Remove overdue courses from the current progress tracking
                    for overdue_course in overdue_courses:
                        overdue_course_id = overdue_course.get('id')
                        if overdue_course_id and overdue_course_id in st.session_state.learning_path_progress[selected_emp_id]:
                            del st.session_state.learning_path_progress[selected_emp_id][overdue_course_id]
                    
                    # Collect skills from overdue courses and remaining path
                    skills_to_cover = set()
                    for oc in overdue_courses:
                        skills_to_cover.update(oc.get('skills_gained', []))
                        if oc.get('title'):
                            skills_to_cover.add(oc['title'].split(' ')[0]) 
                    
                    # Also include skills from remaining uncompleted courses (excluding overdue ones)
                    overdue_course_ids = {oc.get('id') for oc in overdue_courses}
                    for course in all_courses_in_path:
                        course_id = course.get('id')
                        if course_id not in overdue_course_ids:  # Skip overdue courses
                            status_info = progress_data.get(course_id, {})
                            if status_info.get('status') != 'Completed':
                                skills_to_cover.update(course.get('skills_gained', []))
                                if course.get('title'):
                                    skills_to_cover.add(course['title'].split(' ')[0])

                    # Create a learning preference object for shorter duration
                    original_duration = assigned_path.get('total_duration_weeks', 20)
                    new_time_available = max(4, original_duration - 4)

                    shorter_preferences = LearningPreference(
                        time_available_weeks=new_time_available,
                        preferred_learning_style=st.session_state.learning_preferences.preferred_learning_style,
                        difficulty_preference=st.session_state.learning_preferences.difficulty_preference,
                        specific_skills_requested=list(skills_to_cover),
                        learning_urgency="High"
                    )

                    new_learning_path = generate_enhanced_learning_path_with_sync(
                        emp_data,
                        shorter_preferences,
                        specific_requirements={"shorten_duration": True, "skills_to_focus": list(skills_to_cover)}
                    )
                    
                    if new_learning_path:
                        assign_learning_path_to_employee(selected_emp_id, new_learning_path)
                        # Re-initialize progress for the new path
                        st.session_state.learning_path_progress[selected_emp_id] = {}
                        for course in new_learning_path.get('learning_path', []):
                            course_id = course.get('id')
                            if course_id:
                                st.session_state.learning_path_progress[selected_emp_id][course_id] = {
                                    "status": "Not Started", 
                                    "start_date": datetime.now().isoformat(),
                                    "completion_date": None
                                }
                        for course in new_learning_path.get('udemy_courses', []):
                            course_id = course.get('id')
                            if course_id:
                                st.session_state.learning_path_progress[selected_emp_id][course_id] = {
                                    "status": "Not Started", 
                                    "start_date": datetime.now().isoformat(),
                                    "completion_date": None
                                }
                        st.success(f"✅ Shorter learning path generated and assigned to {emp_data['name']}!")
                        st.rerun()
                    else:
                        st.error(f"Failed to regenerate shorter learning path for {emp_data['name']}.")


def display_courses(courses, progress_data, path_start_date, course_type):
    """Helper function to display courses in a consistent format"""
    if not courses:
        return
        
    for course in courses:
        course_id = course.get('id')
        if not course_id:
            course_id = f"generated_{str(uuid.uuid4())}"
            course['id'] = course_id
        
        status_info = progress_data.get(course_id, {"status": "Not Started", "start_date": None, "completion_date": None})
        
        display_status = status_info['status']
        status_emoji = "⚪"
        if display_status == "Completed":
            status_emoji = "✅"
        elif display_status == "In Progress":
            status_emoji = "⏳"

        # Calculate expected completion date
        expected_completion_date = None
        course_duration_weeks = course.get('duration_weeks', 2)  # Default to 2 weeks
        
        # Use individual course start date if available, otherwise use path start date
        if status_info.get('start_date') and status_info['start_date'] is not None:
            course_start = datetime.fromisoformat(status_info['start_date'])
            expected_completion_date = course_start + timedelta(weeks=course_duration_weeks)
        elif path_start_date:
            # For courses without individual start dates, calculate based on path start date
            expected_completion_date = path_start_date + timedelta(weeks=course_duration_weeks)

        is_overdue = False
        if (display_status != "Completed" and 
            expected_completion_date and 
            datetime.now() > expected_completion_date):
            is_overdue = True
            status_emoji = "🚨"

        # Course card layout
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{status_emoji} {course.get('title')}**")
                st.caption(f"Duration: {course.get('duration')} | Status: {display_status}")
                
                if course.get('skills_gained'):
                    skills_text = ", ".join(course['skills_gained'][:3])
                    if len(course['skills_gained']) > 3:
                        skills_text += f" +{len(course['skills_gained']) - 3} more"
                    st.caption(f"Skills: {skills_text}")
            
            with col2:
                if is_overdue:
                    st.error(f"**OVERDUE!**")
                    st.caption(f"Expected: {expected_completion_date.strftime('%Y-%m-%d')}")
                elif expected_completion_date and display_status != "Completed":
                    st.info(f"Due: {expected_completion_date.strftime('%Y-%m-%d')}")
                elif display_status == "Completed" and status_info.get('completion_date'):
                    completion_date = datetime.fromisoformat(status_info['completion_date'])
                    st.success(f"✅ {completion_date.strftime('%Y-%m-%d')}")
        
        st.markdown("---")

# 5. Modify the main function to add page navigation

def main_with_navigation():
    """Main function with navigation between Manager, Employee, Admin, and Dashboard portals"""
    
    # Initialize both session states
    initialize_session_state()
    initialize_manager_session_state()
    
    # Navigation
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧭 Portal Navigation")
    
    portal_mode = st.sidebar.radio(
        "Select Portal:",
        ["🏢 Admin/HR Portal", "👨‍💼 Manager Portal", "👤 Employee Portal", "📈 Dashboard"],
        index=0 if st.session_state.admin_mode else (1 if st.session_state.manager_mode else 2)
    )
    
    # Update session state page and other mode flags
    st.session_state.page = portal_mode
    st.session_state.admin_mode = (portal_mode == "🏢 Admin/HR Portal")
    st.session_state.manager_mode = (portal_mode == "👨‍💼 Manager Portal")

    if st.session_state.page == "🏢 Admin/HR Portal":
        admin_hr_portal_page()
    elif st.session_state.page == "👨‍💼 Manager Portal":
        manager_portal_page()
    elif st.session_state.page == "📈 Dashboard":
        dashboard_page()
    else: # Employee Portal
        # If no employee profile exists, try to load from selected employee
        # This part ensures that if a manager/admin selects an Pemployee,
        # that employee's profile is loaded when switching to Employee Portal
        if 'employee_profile' not in st.session_state or not st.session_state.employee_profile.get('employee_id'):
            if st.session_state.selected_employee_id and st.session_state.selected_employee_id in st.session_state.employee_database:
                st.session_state.employee_profile = st.session_state.employee_database[st.session_state.selected_employee_id].copy()
            else:
                # Fallback to a default employee if no specific one is selected
                default_emp_id = list(st.session_state.employee_database.keys())[0]
                st.session_state.employee_profile = st.session_state.employee_database[default_emp_id].copy()


        # Sync learning path from employee database if available
        current_employee_id = get_current_employee_id()
        if current_employee_id and current_employee_id in st.session_state.employee_database:
            # Always sync the latest learning path from the database
            assigned_path = st.session_state.employee_database[current_employee_id].get('assigned_learning_path')
            if assigned_path:
                st.session_state.learning_path = assigned_path
                
                # Update employee profile to reflect database state
                st.session_state.employee_profile.update(st.session_state.employee_database[current_employee_id])
                
                # Add welcome message only once
                if not any("manager assigned" in msg.get("content", "") for msg in st.session_state.messages):
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"👋 Welcome back! Your manager/admin has assigned you a personalized learning path. You can view it on the right panel and chat with me to modify or get more information about it."
                    })
        
        enhanced_main()


# extra

# Add this enhanced version of generate_enhanced_learning_path that includes sync
def generate_enhanced_learning_path_with_sync(employee_profile, learning_preferences,specific_requirements=None):
    """Generate learning path and sync with employee database"""
    
    # Generate the learning path using the existing function
    learning_path = generate_enhanced_learning_path(employee_profile, learning_preferences,specific_requirements)
    
    # Sync with employee database if employee ID is available
    employee_id = employee_profile.get('employee_id') # Use the employee_id from the profile passed
    if employee_id and learning_path:
        sync_employee_learning_path(employee_id, learning_path)
    
    return learning_path

## report 

import json
from datetime import datetime, timedelta
import base64

def generate_dynamic_learning_report(learning_path, employee_profile, learning_preferences=None):
    """Generate a comprehensive dynamic HTML report for learning path"""
    
    # Extract data for the report
    current_date = datetime.now()
    employee_name = employee_profile.get('name', 'Employee')
    current_role = employee_profile.get('current_role', 'Current Role')
    
    target_role = employee_profile.get('career_goals', ['Target Role']) # Ensure it's a list
    
    # Calculate metrics
    total_weeks = learning_path.get("total_duration_weeks", 12)
    skills_addressed = learning_path.get("skill_gaps_addressed", [])
    udemy_courses = learning_path.get("udemy_courses", [])
    internal_courses = learning_path.get("learning_path", [])
    
    # Calculate financial metrics
    budget = 2000#learning_preferences.budget if learning_preferences else 2000
    estimated_cost = len(udemy_courses) * 50 + len(internal_courses) * 25  # Rough estimate
    roi_percentage = ((budget - estimated_cost) / estimated_cost * 100) if estimated_cost > 0 else 1200
    
    # Generate skill proficiency data for report
    # This will now use the calculate_skill_gaps function for more accurate data
    current_role_reqs = role_requirements.get(employee_profile['current_role'], {})
    career_goal_reqs_list = []
    for goal in employee_profile['career_goals']:
        career_goal_reqs_list.append(role_requirements.get(goal, {}))

    skill_data = calculate_skill_gaps(
        employee_profile,
        current_role_reqs,
        career_goal_reqs_list
    )
    
    # Create the HTML report
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Learning Path Report - {employee_name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            text-align: center;
        }}
        
        .header h1 {{
            color: #2d3748;
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .header-meta {{
            display: flex;
            justify-content: space-between;
            margin-top: 20px;
            flex-wrap: wrap;
            gap: 10px;
        }}
        
        .meta-item {{
            background: #f7fafc;
            padding: 10px 15px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }}
        
        .section {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .section:hover {{
            transform: translateY(-5px);
            box-shadow: 0 25px 30px -5px rgba(0, 0, 0, 0.15);
        }}
        
        .section-title {{
            color: #2d3748;
            font-size: 1.8rem;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .metric-card {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .metric-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }}
        
        .metric-card:hover::before {{
            left: 100%;
        }}
        
        .metric-card:hover {{
            transform: scale(1.05);
            box-shadow: 0 15px 30px rgba(0, 0, 0, 0.2);
        }}
        
        .metric-value {{
            font-size: 2.5rem;
            font-weight: bold;
            display: block;
        }}
        
        .metric-label {{
            font-size: 0.9rem;
            opacity: 0.9;
            margin-top: 5px;
        }}
        
        .progress-bar {{
            background: #e2e8f0;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
            position: relative;
        }}
        
        .progress-fill {{
            height: 20px;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 10px;
            transition: width 2s ease;
            position: relative;
        }}
        
        .progress-fill::after {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            bottom: 0;
            right: 0;
            background-image: linear-gradient(
                45deg,
                rgba(255, 255, 255, 0.2) 25%,
                transparent 25%,
                transparent 50%,
                rgba(255, 255, 255, 0.2) 50%,
                rgba(255, 255, 255, 0.2) 75%,
                transparent 75%,
                transparent
            );
            background-size: 20px 20px;
            animation: move 1s linear infinite;
        }}
        
        @keyframes move {{
            0% {{ background-position: 0 0; }}
            100% {{ background-position: 20px 20px; }}
        }}
        
        .skill-gap-analysis {{
            padding: 20px;
        }}
        
        .icon-large {{
            font-size: 3rem;
            margin-bottom: 10px;
        }}
        
        .skills-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        
        .skill-item {{
            background: #f7fafc;
            border-radius: 15px;
            padding: 20px;
            border-left: 5px solid #667eea;
            transition: all 0.3s ease;
        }}
        
        .skill-item:hover {{
            background: #edf2f7;
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        }}
        
        .skill-current {{
            border-left-color: #48bb78;
            background: linear-gradient(135deg, rgba(72, 187, 120, 0.1), rgba(56, 161, 105, 0.05));
        }}
        
        .skill-gap-critical {{
            border-left-color: #e53e3e;
            background: linear-gradient(135deg, rgba(229, 62, 62, 0.1), rgba(197, 48, 48, 0.05));
        }}
        
        .skill-gap-important {{
            border-left-color: #ed8936;
            background: linear-gradient(135deg, rgba(237, 137, 54, 0.1), rgba(221, 107, 32, 0.05));
        }}
        
        .skill-proficiency {{
            margin: 15px 0;
        }}
        
        .proficiency-bar {{
            background: #e2e8f0;
            border-radius: 10px;
            height: 8px;
            overflow: hidden;
            margin: 5px 0;
        }}
        
        .proficiency-fill {{
            height: 100%;
            border-radius: 10px;
            transition: width 2s ease;
        }}
        
        .proficiency-fill.advanced {{
            background: linear-gradient(90deg, #48bb78, #38a169);
            width: 85%;
        }}
        
        .proficiency-fill.beginner {{
            background: linear-gradient(90deg, #e53e3e, #c53030);
            width: 15%;
        }}
        
        .proficiency-fill.intermediate {{
            background: linear-gradient(90deg, #ed8936, #dd6b20);
            width: 35%;
        }}
        
        .highlight-box {{
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.05));
            border: 2px solid #667eea;
            border-radius: 15px;
            padding: 25px;
            margin-top: 30px;
            text-align: center;
        }}
        
        .progress-indicator {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin: 10px 0;
            justify-content: center;
        }}
        
        .progress-indicator span {{
            min-width: 60px;
            font-weight: 600;
        }}
        
        .timeline {{
            position: relative;
            padding-left: 30px;
        }}
        
        .timeline::before {{
            content: '';
            position: absolute;
            left: 15px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: linear-gradient(to bottom, #667eea, #764ba2);
        }}
        
        .timeline-item {{
            position: relative;
            margin-bottom: 30px;
            background: #f7fafc;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }}
        
        .timeline-item::before {{
            content: '';
            position: absolute;
            left: -35px;
            top: 25px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #667eea;
            border: 3px solid white;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
        }}
        
        .course-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .course-card {{
            background: #f7fafc;
            border-radius: 15px;
            padding: 20px;
            border-left: 4px solid #667eea;
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        
        .course-card:hover {{
            background: #edf2f7;
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        }}
        
        .comparison-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }}
        
        .comparison-table th,
        .comparison-table td {{
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .comparison-table th {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            font-weight: 600;
        }}
        
        .comparison-table tr:hover {{
            background: #f7fafc;
        }}
        
        .roi-highlight {{
            background: linear-gradient(135deg, #48bb78, #38a169);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            margin: 20px 0;
        }}
        
        .interactive-tooltip {{
            position: relative;
            cursor: help;
        }}
        
        .interactive-tooltip:hover::after {{
            content: attr(data-tooltip);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: #2d3748;
            color: white;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 0.8rem;
            white-space: nowrap;
            z-index: 1000;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
            
            .metrics-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header-meta {{
                flex-direction: column;
            }}
        }}
        
        .fade-in {{
            animation: fadeIn 0.6s ease-in;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header fade-in">
            <h1>🎓 Learning Path Report</h1>
            <p><strong>{employee_name}</strong> • {current_role} → {target_role[0]}</p>
            <div class="header-meta">
                <div class="meta-item">
                    <strong>Generated:</strong> {current_date.strftime('%B %d, %Y')}
                </div>
                <div class="meta-item">
                    <strong>Duration:</strong> {total_weeks} weeks
                </div>
                <div class="meta-item">
                    <strong>Completion Target:</strong> {(current_date + timedelta(weeks=total_weeks)).strftime('%B %d, %Y')}
                </div>
            </div>
        </div>

        <div class="section fade-in">
            <h2 class="section-title">👤 Detailed Employee Profile</h2>
            <div class="metrics-grid">
                <div class="metric-card interactive-tooltip" data-tooltip="Current professional level">
                    <span class="metric-value">📊</span>
                    <span class="metric-label">Current Role</span>
                    <div>{current_role}</div>
                </div>
                <div class="metric-card interactive-tooltip" data-tooltip="Target career goal">
                    <span class="metric-value">🎯</span>
                    <span class="metric-label">Target Role</span>
                    <div>{target_role[0]}</div>
                </div>
                <div class="metric-card interactive-tooltip" data-tooltip="Available learning budget">
                    <span class="metric-value">${budget:,}</span>
                    <span class="metric-label">Learning Budget</span>
                </div>
                <div class="metric-card interactive-tooltip" data-tooltip="Projected timeline for role transition">
                    <span class="metric-value">{total_weeks}</span>
                    <span class="metric-label">Weeks to Target</span>
                </div>
            </div>
            
            <div style="margin-top: 20px;">
                <h3>📋 Background Information</h3>
                <p><strong>Experience Level:</strong> {employee_profile.get('experience_level', 'Mid-level')}</p>
                <p><strong>Department:</strong> {employee_profile.get('department', 'Technology')}</p>
                <p><strong>Learning Style:</strong> {learning_preferences.preferred_learning_style if learning_preferences else 'Mixed'}</p>
                <p><strong>Time Availability:</strong> {learning_preferences.time_available_weeks if learning_preferences else '10'} hours/week</p>
            </div>
        </div>

        <div class="section fade-in">
            <div class="skill-gap-analysis">
                <div class="icon-large" style="text-align: center;">📊</div>
                <h3 style="text-align: center; margin-bottom: 20px;">Advanced Skill Gap Analysis</h3>
                <div class="skills-grid">
                    {generate_dynamic_skill_categories_html(skill_data)}
                </div>
                <div class="highlight-box">
                    <h4>🎯 Gap Analysis Summary</h4>
                    <p><strong>Skill Coverage for Target Role:</strong> 45% → Target: 85%</p>
                    <div class="progress-indicator">
                        <span>Current</span>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: 45%;"></div>
                        </div>
                        <span>45%</span>
                    </div>
                    <div class="progress-indicator">
                        <span>Target</span>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: 85%;"></div>
                        </div>
                        <span>85%</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="section fade-in">
            <h2 class="section-title">⏰ Comprehensive {total_weeks}-Week Learning Timeline</h2>
            
            <div class="timeline">
                {generate_timeline_html(internal_courses, udemy_courses, total_weeks)}
            </div>
        </div>

        <div class="section fade-in">
            <h2 class="section-title">📚 Course Portfolio</h2>
            
            <h3>🏢 Internal Courses ({len(internal_courses)})</h3>
            <div class="course-grid">
                {generate_internal_courses_html(internal_courses)}
            </div>
            
            <h3 style="margin-top: 30px;">🌟 Udemy Courses ({len(udemy_courses)})</h3>
            <div class="course-grid">
                {generate_udemy_courses_html(udemy_courses)}
            </div>
        </div>

        <div class="section fade-in">
            <h2 class="section-title">💼 Business Impact & ROI Analysis</h2>
            
            
            
            <div class="metrics-grid">
                <div class="metric-card" style="background: linear-gradient(135deg, #48bb78, #38a169);">
                    <span class="metric-value">3</span>
                    <span class="metric-label">Portfolio Projects</span>
                </div>
                <div class="metric-card" style="background: linear-gradient(135deg, #ed8936, #dd6b20);">
                    <span class="metric-value">4</span>
                    <span class="metric-label">Certifications</span>
                </div>
                <div class="metric-card" style="background: linear-gradient(135deg, #3182ce, #2c5282);">
                    <span class="metric-value">85%</span>
                    <span class="metric-label">Target Competency</span>
                </div>
                <div class="metric-card" style="background: linear-gradient(135deg, #805ad5, #6b46c1);">
                    <span class="metric-value">12</span>
                    <span class="metric-label">Week Checkpoints</span>
                </div>
            </div>

            <h3 style="margin-top: 30px;">📈 Competency Comparison</h3>
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th>Competency Area</th>
                        <th>Current Level</th>
                        <th>Target Level</th>
                        <th>Post-Training</th>
                        <th>Gap Closure</th>
                    </tr>
                </thead>
                <tbody>
                    {generate_competency_table_html(skill_data)}
                </tbody>
            </table>
        </div>

        <div class="section fade-in">
            <h2 class="section-title">🏆 Milestone Checkpoints</h2>
            
            <div class="timeline">
                <div class="timeline-item">
                    <h4>Week 4 Checkpoint 🎯</h4>
                    <p><strong>Goal:</strong> Complete foundation courses and first assessment</p>
                    <p><strong>Deliverable:</strong> Basic project demonstration</p>
                    <p><strong>Skills Gained:</strong> Fundamental concepts, basic implementation</p>
                </div>
                <div class="timeline-item">
                    <h4>Week 8 Checkpoint 🚀</h4>
                    <p><strong>Goal:</strong> Advanced skill development and mid-term evaluation</p>
                    <p><strong>Deliverable:</strong> Intermediate project portfolio</p>
                    <p><strong>Skills Gained:</strong> Advanced techniques, practical application</p>
                </div>
                <div class="timeline-item">
                    <h4>Week {total_weeks} Checkpoint 🎓</h4>
                    <p><strong>Goal:</strong> Final assessment and role readiness evaluation</p>
                    <p><strong>Deliverable:</strong> Comprehensive capstone project</p>
                    <p><strong>Skills Gained:</strong> Expert-level proficiency, leadership capabilities</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Add interactive animations
        document.addEventListener('DOMContentLoaded', function() {{
            // Animate progress bars
            const progressBars = document.querySelectorAll('.progress-fill');
            progressBars.forEach(bar => {{
                const width = bar.dataset.width;
                setTimeout(() => {{
                    bar.style.width = width + '%';
                }}, 500);
            }});
            
            // Add click feedback to metric cards
            const metricCards = document.querySelectorAll('.metric-card');
            metricCards.forEach(card => {{
                card.addEventListener('click', function() {{
                    this.style.transform = 'scale(0.95)';
                    setTimeout(() => {{
                        this.style.transform = 'scale(1.05)';
                    }}, 150);
                }});
            }});
            
            // Fade in sections on scroll
            const observer = new IntersectionObserver((entries) => {{
                entries.forEach(entry => {{
                    if (entry.isIntersecting) {{
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }}
                }});
            }});
            
            document.querySelectorAll('.section').forEach(section => {{
                section.style.opacity = '0';
                section.style.transform = 'translateY(20px)';
                section.style.transition = 'all 0.6s ease';
                observer.observe(section);
            }});
        }});
    </script>
</body>
</html>
    """
    
    return html_content

def get_proficiency_value(proficiency_label: str) -> int:
    """Maps proficiency labels to a numerical value for comparison."""
    proficiency_map = {
        "Beginner": 1,
        "Intermediate": 2,
        "Advanced": 3,
        "Expert": 4
    }
    return proficiency_map.get(proficiency_label, 0) # Default to 0 for unknown

def get_proficiency_label_from_value(value: int) -> str:
    """Maps numerical value back to proficiency label."""
    proficiency_map = {
        1: "Beginner",
        2: "Intermediate",
        3: "Advanced",
        4: "Expert"
    }
    return proficiency_map.get(value, "Unknown")

def calculate_skill_gaps(employee_profile: Dict, current_role_reqs: Dict, career_goal_reqs_list: List[Dict]) -> List[Dict]:
    """
    Calculates skill gaps based on current proficiency vs. target role requirements.
    Returns a list of dictionaries, each representing a skill gap.
    """
    skill_gaps_data = []
    employee_proficiency = employee_profile.get("skill_proficiency", {})
    
    # Combine required and preferred skills from current role and all career goals
    target_skills_with_proficiency = {}
    
    # Add skills from current role requirements
    for skill, proficiency in current_role_reqs.get("required_skills", {}).items():
        target_skills_with_proficiency[skill] = max(
            get_proficiency_value(target_skills_with_proficiency.get(skill, "Beginner")),
            get_proficiency_value(proficiency)
        )
    for skill, proficiency in current_role_reqs.get("preferred_skills", {}).items():
        target_skills_with_proficiency[skill] = max(
            get_proficiency_value(target_skills_with_proficiency.get(skill, "Beginner")),
            get_proficiency_value(proficiency)
        )

    # Add skills from career goal requirements
    for goal_reqs in career_goal_reqs_list:
        for skill, proficiency in goal_reqs.get("required_skills", {}).items():
            target_skills_with_proficiency[skill] = max(
                get_proficiency_value(target_skills_with_proficiency.get(skill, "Beginner")),
                get_proficiency_value(proficiency)
            )
        for skill, proficiency in goal_reqs.get("preferred_skills", {}).items():
            target_skills_with_proficiency[skill] = max(
                get_proficiency_value(target_skills_with_proficiency.get(skill, "Beginner")),
                get_proficiency_value(proficiency)
            )

    for skill, target_proficiency_value in target_skills_with_proficiency.items():
        current_proficiency_label = employee_proficiency.get(skill, "Beginner")
        current_proficiency_value = get_proficiency_value(current_proficiency_label)

        if current_proficiency_value < target_proficiency_value:
            skill_gaps_data.append({
                "Skill": skill,
                "Current Proficiency": current_proficiency_label,
                "Target Proficiency": get_proficiency_label_from_value(target_proficiency_value),
                "Gap": f"{current_proficiency_label} to {get_proficiency_label_from_value(target_proficiency_value)}"
            })
    
    return skill_gaps_data

def generate_dynamic_skill_categories_html(skill_data):
    """Generate dynamic HTML for skill categories based on proficiency levels"""
    
    # Categorize skills based on proficiency
    # These are illustrative categories for the report, based on the 'Gap' identified
    current_strengths = [s for s in skill_data if s['Current Proficiency'] == s['Target Proficiency']]
    critical_gaps = [s for s in skill_data if get_proficiency_value(s['Target Proficiency']) - get_proficiency_value(s['Current Proficiency']) >= 2] # Gap of 2 levels or more
    important_gaps = [s for s in skill_data if get_proficiency_value(s['Target Proficiency']) - get_proficiency_value(s['Current Proficiency']) == 1] # Gap of 1 level

    # Ensure some data for display if categories are empty
    if not current_strengths:
        current_strengths = [{'Skill': 'Communication', 'Current Proficiency': 'Advanced', 'Target Proficiency': 'Advanced', 'Gap': 'None'}]
    if not critical_gaps:
        critical_gaps = [{'Skill': 'Cloud Security', 'Current Proficiency': 'Beginner', 'Target Proficiency': 'Advanced', 'Gap': 'Beginner to Advanced'}]
    if not important_gaps:
        important_gaps = [{'Skill': 'Project Management', 'Current Proficiency': 'Beginner', 'Target Proficiency': 'Intermediate', 'Gap': 'Beginner to Intermediate'}]
    
    html = f"""
    <div class="skill-item skill-current">
        <h4>✅ Current Strengths</h4>
        <div class="skill-proficiency">
            <div class="proficiency-bar">
                <div class="proficiency-fill advanced"></div>
            </div>
        </div>
        {generate_skill_list_html(current_strengths, 'strength')}
    </div>
    
    <div class="skill-item skill-gap-critical">
        <h4>🚨 Critical Gaps</h4>
        <div class="skill-proficiency">
            <div class="proficiency-bar">
                <div class="proficiency-fill beginner"></div>
            </div>
        </div>
        {generate_skill_list_html(critical_gaps, 'critical')}
    </div>
    
    <div class="skill-item skill-gap-important">
        <h4>⚠️ Important Gaps</h4>
        <div class="skill-proficiency">
            <div class="proficiency-bar">
                <div class="proficiency-fill intermediate"></div>
            </div>
        </div>
        {generate_skill_list_html(important_gaps, 'important')}
    </div>
    """
    
    return html

def generate_skill_list_html(skills, category_type):
    """Generate HTML for individual skill items within a category"""
    html = ""
    
    for skill_info in skills:
        skill_name = skill_info['Skill']
        current_prof = skill_info['Current Proficiency']
        target_prof = skill_info['Target Proficiency']
        gap_text = skill_info['Gap']

        html += f'<p><strong>{skill_name}:</strong> Current: {current_prof}, Target: {target_prof} ({gap_text})</p>'
    
    return html

def generate_timeline_html(internal_courses, udemy_courses, total_weeks):
    """Generate timeline HTML"""
    timeline_html = ""
    weeks_per_phase = max(1, total_weeks // 3)
    
    phases = [
        ("Foundation Phase", f"Weeks 1-{weeks_per_phase}", "Building core competencies"),
        ("Development Phase", f"Weeks {weeks_per_phase+1}-{weeks_per_phase*2}", "Advanced skill development"),
        ("Mastery Phase", f"Weeks {weeks_per_phase*2+1}-{total_weeks}", "Expert-level proficiency")
    ]
    
    for i, (phase_name, duration, description) in enumerate(phases):
        courses_in_phase = internal_courses[i::3] + udemy_courses[i::3]  # Distribute courses
        
        timeline_html += f"""
        <div class="timeline-item">
            <h4>{phase_name}</h4>
            <p><strong>Duration:</strong> {duration}</p>
            <p><strong>Focus:</strong> {description}</p>
            <p><strong>Courses:</strong> {len(courses_in_phase)} courses assigned</p>
            <div style="margin-top: 10px;">
                <div class="progress-bar">
                    <div class="progress-fill" data-width="{(i+1)*33}" style="width: 0%;"></div>
                </div>
            </div>
        </div>
        """
    
    return timeline_html

def generate_internal_courses_html(courses):
    """Generate HTML for internal courses"""
    html = ""
    for course in courses[:6]:  # Limit display
        priority_emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(course.get('priority', 'Medium'), "⚪")
        
        html += f"""
        <div class="course-card">
            <h4>{course.get('title', 'Course Title')} {priority_emoji}</h4>
            <p><strong>Type:</strong> {course.get('type', 'Training')}</p>
            <p><strong>Duration:</strong> {course.get('duration', 'N/A')}</p>
            <p><strong>Priority:</strong> {course.get('priority', 'Medium')}</p>
            <p><strong>Skills:</strong> {', '.join(course.get('skills_gained', []))}</p>
            <small style="color: #666;">{course.get('reason', 'Strategic skill development')}</small>
        </div>
        """
    
    return html

def generate_udemy_courses_html(courses):
    """Generate HTML for Udemy courses"""
    html = ""
    for course in courses[:6]:  # Limit display
        stars = "⭐" * int(course.get('rating', 4))
        
        html += f"""
        <div class="course-card">
            <h4>{course.get('title', 'Course Title')}</h4>
            <p><strong>Rating:</strong> {stars} {course.get('rating', 4.0)}</p>
            <p><strong>Price:</strong> {course.get('price', 'N/A')}</p>
            <p><strong>Duration:</strong> {course.get('duration', 'N/A')}</p>
            <p><strong>Level:</strong> {course.get('level', 'Intermediate')}</p>
            <small style="color: #666;">{course.get('description', 'No description available.')[:100]}...</small>
        </div>
        """
    
    return html

def generate_competency_table_html(skill_data):
    """Generate competency comparison table HTML"""
    html = ""
    # Use the skill_data from calculate_skill_gaps
    for skill_info in skill_data[:8]:  # Limit to 8 skills
        skill_name = skill_info['Skill']
        current_prof_label = skill_info['Current Proficiency']
        target_prof_label = skill_info['Target Proficiency']
        
        # Mock post-training and gap closure for report visualization
        current_val = get_proficiency_value(current_prof_label)
        target_val = get_proficiency_value(target_prof_label)
        
        post_training_val = min(4, current_val + 1) # Assume at least one level up
        if current_val == target_val: # If no gap, assume already met target
            post_training_val = target_val
        
        gap_closure_percentage = 0
        if target_val > current_val:
            gap_closure_percentage = ((post_training_val - current_val) / (target_val - current_val)) * 100
            gap_closure_percentage = min(100, int(gap_closure_percentage)) # Cap at 100%
        else:
            gap_closure_percentage = 100 # Already met or exceeded target

        html += f"""
        <tr>
            <td><strong>{skill_name}</strong></td>
            <td>{current_prof_label}</td>
            <td>{target_prof_label}</td>
            <td>{get_proficiency_label_from_value(post_training_val)}</td>
            <td style="color: #48bb78; font-weight: bold;">{gap_closure_percentage:.0f}%</td>
        </tr>
        """
    
    return html

# Enhanced learning path management in employee portal
def enhanced_learning_path_management():
    """Enhanced learning path management with database synchronization and course selection"""
    
    current_employee_id = get_current_employee_id()

    if not current_employee_id:
        st.warning("Please select an employee or ensure your profile is loaded to view learning paths.")
        return

    # Ensure learning_path is loaded from the database for the current employee
    if current_employee_id in st.session_state.employee_database:
        st.session_state.learning_path = st.session_state.employee_database[current_employee_id].get('assigned_learning_path')
    else:
        st.session_state.learning_path = None # No path if employee not in DB

    if st.session_state.learning_path:
        st.markdown("### 📚 Your Learning Path")
        
        # Check if this is a manager-assigned path
        is_manager_assigned = False
        if current_employee_id and current_employee_id in st.session_state.employee_database:
            db_path = st.session_state.employee_database[current_employee_id].get('assigned_learning_path')
            is_manager_assigned = (db_path is not None)
        
        if is_manager_assigned:
            st.info("📋 This learning path was assigned by your manager/admin and is synchronized across both portals.")
        
        # --- Course Selection Interface ---
        st.markdown("#### ✅ Select Courses for Your Final Plan")
        
        # Initialize selected courses for plan if not exists
        if 'selected_courses_for_plan' not in st.session_state:
            st.session_state.selected_courses_for_plan = {}
        
        if current_employee_id not in st.session_state.selected_courses_for_plan:
            st.session_state.selected_courses_for_plan[current_employee_id] = {}
            # Initialize all courses as selected by default
            for course in st.session_state.learning_path.get('learning_path', []):
                course_id = course.get('id', f"internal_{str(uuid.uuid4())}") # Ensure ID for internal courses
                course['id'] = course_id # Add ID to the course in the assigned path
                st.session_state.selected_courses_for_plan[current_employee_id][course_id] = True
            for course in st.session_state.learning_path.get('udemy_courses', []):
                if 'id' not in course:
                    course['id'] = f"udemy_{str(uuid.uuid4())}" # Ensure ID for Udemy courses
                st.session_state.selected_courses_for_plan[current_employee_id][course['id']] = True

        # Initialize learning path progress for this employee if not present
        if current_employee_id not in st.session_state.learning_path_progress:
            st.session_state.learning_path_progress[current_employee_id] = {}
            for course in st.session_state.learning_path.get('learning_path', []):
                course_id = course.get('id')
                if course_id:
                    st.session_state.learning_path_progress[current_employee_id][course_id] = {
                        "status": "Not Started", 
                        "start_date": None, 
                        "completion_date": None
                    }
            for course in st.session_state.learning_path.get('udemy_courses', []):
                course_id = course.get('id')
                if course_id:
                    st.session_state.learning_path_progress[current_employee_id][course_id] = {
                        "status": "Not Started", 
                        "start_date": None, 
                        "completion_date": None
                    }


        selected_internal_courses = []
        selected_udemy_courses = []
        total_selected_duration = 0
        total_selected_skills = set()

        # Internal Courses Selection
        st.markdown("##### Internal Courses")
        for i, course in enumerate(st.session_state.learning_path.get("learning_path", [])):
            course_id = course.get('id') # Already ensured to have ID above
            
            # Get current progress status
            current_status_info = st.session_state.learning_path_progress[current_employee_id].get(course_id, {"status": "Not Started"})
            is_completed = (current_status_info["status"] == "Completed")

            checkbox_key = f"select_internal_{course_id}_{current_employee_id}"
            completion_checkbox_key = f"complete_internal_{course_id}_{current_employee_id}"
            
            col_sel, col_title, col_comp = st.columns([0.5, 4, 1])
            with col_sel:
                # Course selection checkbox
                is_selected = st.checkbox(
                    "",
                    value=st.session_state.selected_courses_for_plan[current_employee_id].get(course_id, True),
                    key=checkbox_key
                )
            with col_title:
                st.markdown(f"**{course.get('title')}** ({course.get('duration')})")
            with col_comp:
                # Completion checkbox
                new_is_completed = st.checkbox(
                    "Completed",
                    value=is_completed,
                    key=completion_checkbox_key
                )

            # Update selection state
            st.session_state.selected_courses_for_plan[current_employee_id][course_id] = is_selected
            
            # Update completion status
            if new_is_completed and not is_completed: # Just marked complete
                st.session_state.learning_path_progress[current_employee_id][course_id] = {
                    "status": "Completed",
                    "start_date": current_status_info.get("start_date") or datetime.now().isoformat(),
                    "completion_date": datetime.now().isoformat()
                }
                st.success(f"Marked '{course.get('title')}' as Completed!")
            elif not new_is_completed and is_completed: # Just unchecked complete
                st.session_state.learning_path_progress[current_employee_id][course_id] = {
                    "status": "Not Started", # Reset to Not Started
                    "start_date": None,
                    "completion_date": None
                }
                st.info(f"Marked '{course.get('title')}' as Not Started.")
            elif new_is_completed and is_completed: # Still completed, ensure start date is there
                if not current_status_info.get("start_date"):
                     st.session_state.learning_path_progress[current_employee_id][course_id]["start_date"] = datetime.now().isoformat()
            elif not new_is_completed and not is_completed: # Still not completed, ensure start date is set if user interacted
                if st.session_state.learning_path_progress[current_employee_id].get(course_id, {}).get("status") == "Not Started" and \
                   st.session_state.learning_path_progress[current_employee_id].get(course_id, {}).get("start_date") is None:
                    # If user didn't mark as completed but interacted, assume they started
                    st.session_state.learning_path_progress[current_employee_id][course_id]["status"] = "In Progress"
                    st.session_state.learning_path_progress[current_employee_id][course_id]["start_date"] = datetime.now().isoformat()


            if is_selected:
                selected_internal_courses.append(course)
                total_selected_duration += course.get('duration_weeks', 0)
                total_selected_skills.update(course.get('skills_gained', []))
            
            # Show course details (existing functionality)
            with st.container():
                priority_colors = {
                    "Critical": "🔴",
                    "High": "🟠", 
                    "Medium": "🟡",
                    "Low": "🟢"
                }
                priority_emoji = priority_colors.get(course.get("priority", "Medium"), "⚪")
                
                col_x, col_y = st.columns([3, 1])
                with col_x:
                    st.markdown(f"📚 {course.get('type')} • ⏱️ {course.get('duration')}")
                    st.markdown(f"🎯 **Skills:** {', '.join(course.get('skills_gained', []))}")
                with col_y:
                    st.markdown(f"🚨 **{course.get('priority', 'Medium')}** {priority_emoji}")
                
                with st.expander("Details"):
                    st.markdown(f"**Why recommended:** {course.get('reason', 'N/A')}")
                    if course.get('fits_constraints'):
                        st.markdown(f"**Constraint fit:** {course['fits_constraints']}")
                
                st.divider()

        # Udemy Courses Selection
        udemy_courses = st.session_state.learning_path.get("udemy_courses", [])
        if udemy_courses:
            st.markdown("##### Udemy Courses")
            
            for i, course in enumerate(udemy_courses):
                if 'id' not in course:
                    course['id'] = f"udemy_{str(uuid.uuid4())}" # Ensure ID for Udemy courses
                
                course_id = course.get('id')
                # Get current progress status
                current_status_info = st.session_state.learning_path_progress[current_employee_id].get(course_id, {"status": "Not Started"})
                is_completed = (current_status_info["status"] == "Completed")

                checkbox_key = f"select_udemy_{course['id']}_{current_employee_id}"
                completion_checkbox_key = f"complete_udemy_{course_id}_{current_employee_id}"
                
                col_sel, col_title, col_comp = st.columns([0.5, 4, 1])
                with col_sel:
                    # Course selection checkbox
                    is_selected = st.checkbox(
                        "",
                        value=st.session_state.selected_courses_for_plan[current_employee_id].get(course['id'], True),
                        key=checkbox_key
                    )
                with col_title:
                    st.markdown(f"**[{course['title']}]({course['url']})** ({course.get('duration')}) - {course.get('price')}")
                with col_comp:
                    # Completion checkbox
                    new_is_completed = st.checkbox(
                        "Completed",
                        value=is_completed,
                        key=completion_checkbox_key
                    )

                # Update selection state
                st.session_state.selected_courses_for_plan[current_employee_id][course['id']] = is_selected

                # Update completion status
                if new_is_completed and not is_completed: # Just marked complete
                    st.session_state.learning_path_progress[current_employee_id][course_id] = {
                        "status": "Completed",
                        "start_date": current_status_info.get("start_date") or datetime.now().isoformat(),
                        "completion_date": datetime.now().isoformat()
                    }
                    st.success(f"Marked '{course.get('title')}' as Completed!")
                elif not new_is_completed and is_completed: # Just unchecked complete
                    st.session_state.learning_path_progress[current_employee_id][course_id] = {
                        "status": "Not Started", # Reset to Not Started
                        "start_date": None,
                        "completion_date": None
                    }
                    st.info(f"Marked '{course.get('title')}' as Not Started.")
                elif new_is_completed and is_completed: # Still completed, ensure start date is there
                    if not current_status_info.get("start_date"):
                        st.session_state.learning_path_progress[current_employee_id][course_id]["start_date"] = datetime.now().isoformat()
                elif not new_is_completed and not is_completed: # Still not completed, ensure start date is set if user interacted
                    if st.session_state.learning_path_progress[current_employee_id].get(course_id, {}).get("status") == "Not Started" and \
                       st.session_state.learning_path_progress[current_employee_id].get(course_id, {}).get("start_date") is None:
                        # If user didn't mark as completed but interacted, assume they started
                        st.session_state.learning_path_progress[current_employee_id][course_id]["status"] = "In Progress"
                        st.session_state.learning_path_progress[current_employee_id][course_id]["start_date"] = datetime.now().isoformat()


                if is_selected:
                    selected_udemy_courses.append(course)
                    total_selected_duration += course.get('duration_weeks', 0)
                    # Simple skill extraction from title
                    if course.get('title'):
                        total_selected_skills.add(course['title'].split(' ')[0])
                
                # Show course details (existing functionality)
                with st.container():
                    col_title, col_rating = st.columns([3, 1])
                    with col_title:
                        st.markdown(f"**[{course['title']}]({course['url']})**")
                    with col_rating:
                        stars = "⭐" * int(course.get('rating', 4))
                        st.markdown(f"{stars} {course.get('rating', 4.0)}")
                    
                    col_price, col_duration, col_level = st.columns(3)
                    with col_price:
                        st.markdown(f"💰 **{course.get('price', 'N/A')}**")
                    with col_duration:
                        st.markdown(f"⏱️ **{course.get('duration', 'N/A')}**")
                    with col_level:
                        st.markdown(f"📊 **{course.get('level', 'N/A')}**")
                    
                    st.markdown(f"📝 {course.get('description', 'No description available.')}")
                    st.link_button(
                        f"🚀 View Course on Udemy",
                        course.get('url', '#'),
                        help=f"Open {course['title']} on Udemy"
                    )
                    st.divider()

        # Final Plan Summary
        st.markdown("---")
        st.markdown("#### 📊 Final Plan Summary (Selected Courses)")
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Total Duration", f"{total_selected_duration:.1f} weeks")
        with col_b:
            st.metric("Courses", len(selected_internal_courses) + len(selected_udemy_courses))
        with col_c:
            st.metric("Skills Covered", len(total_selected_skills))

        # Overall Path Summary (existing functionality)
        total_weeks = st.session_state.learning_path.get("total_duration_weeks", 0)
        skills_count = len(st.session_state.learning_path.get("skill_gaps_addressed", []))
        udemy_count = len(st.session_state.learning_path.get("udemy_courses", []))
        
        st.markdown("#### 📈 Overall Path Information")
        col_d, col_e, col_f = st.columns(3)
        with col_d:
            st.metric("Available Duration", f"{total_weeks} weeks")
        with col_e:
            st.metric("Available Skills", skills_count)
        with col_f:
            st.metric("Available Udemy Courses", udemy_count)
        
        # Explanation (existing functionality)
        if st.session_state.learning_path.get("explanation"):
            st.info(st.session_state.learning_path["explanation"])
        
        # Additional information (existing functionality)
        if st.session_state.learning_path.get("progression_notes"):
            with st.expander("📝 Learning Progression Notes"):
                st.markdown(st.session_state.learning_path["progression_notes"])
        
        if st.session_state.learning_path.get("alternative_suggestions"):
            with st.expander("💡 Alternative Learning Suggestions"):
                st.markdown(st.session_state.learning_path["alternative_suggestions"])
        
        # Enhanced action buttons with synchronization
        col_1, col_2, col_3, col_4 = st.columns(4)
        
        with col_1:
            if st.button("🔄 Regenerate Path", type="primary", key="regenerate_main"):
                with st.spinner("Regenerating your learning path..."):
                    # Use current employee profile and preferences
                    new_learning_path = generate_enhanced_learning_path_with_sync(
                        st.session_state.employee_profile,
                        st.session_state.get('learning_preferences', LearningPreference())
                    )
                    
                    if new_learning_path:
                        st.success("✅ Learning path regenerated and synchronized!")
                        # Reset progress for the new path
                        st.session_state.learning_path_progress[current_employee_id] = {}
                        for course in new_learning_path.get('learning_path', []):
                            course_id = course.get('id')
                            if course_id:
                                st.session_state.learning_path_progress[current_employee_id][course_id] = {
                                    "status": "Not Started", 
                                    "start_date": None, 
                                    "completion_date": None
                                }
                        for course in new_learning_path.get('udemy_courses', []):
                            course_id = course.get('id')
                            if course_id:
                                st.session_state.learning_path_progress[current_employee_id][course_id] = {
                                    "status": "Not Started", 
                                    "start_date": None, 
                                    "completion_date": None
                                }
                        st.rerun()
                    else:
                        st.error("Failed to regenerate learning path. Please try again.")
        
        with col_2:
            if st.button("📝 Finalize Plan", key="save_final_plan_btn", help="Finalize your selected courses as the official learning path"):
                # Create finalized path data with only selected courses
                finalized_path_data = {
                    "learning_path": selected_internal_courses,
                    "udemy_courses": selected_udemy_courses,
                    "total_duration_weeks": total_selected_duration,
                    "skill_gaps_addressed": list(total_selected_skills),
                    "explanation": st.session_state.learning_path.get("explanation", "Finalized learning path based on your selections."),
                    "progression_notes": st.session_state.learning_path.get("progression_notes", "Courses arranged for optimal learning progression."),
                    "alternative_suggestions": st.session_state.learning_path.get("alternative_suggestions", "No additional alternatives at this time."),
                    "start_date": datetime.now().isoformat() # Add start date when finalized
                }
                
                # Update the learning path with finalized version
                if current_employee_id and sync_employee_learning_path(current_employee_id, finalized_path_data):
                    # Update session state with finalized path
                    st.session_state.learning_path = finalized_path_data
                    st.success("🎉 Your learning plan has been finalized!")
                    st.rerun()
                else:
                    st.error("Failed to finalize plan.")
        
        with col_3:
            if st.button("📊 Download Dynamic Report", help="Generate comprehensive learning path report"):
                with st.spinner("Generating dynamic report..."):
                    try:
                        # Use selected courses for report generation
                        report_data = {
                            "learning_path": selected_internal_courses,
                            "udemy_courses": selected_udemy_courses,
                            "total_duration_weeks": total_selected_duration,
                            "skill_gaps_addressed": list(total_selected_skills),
                            "explanation": st.session_state.learning_path.get("explanation", ""),
                            "progression_notes": st.session_state.learning_path.get("progression_notes", ""),
                            "alternative_suggestions": st.session_state.learning_path.get("alternative_suggestions", "")
                        }
                        
                        # Generate the dynamic HTML report
                        report_html = generate_dynamic_learning_report(
                            report_data,
                            st.session_state.employee_profile,
                            st.session_state.get('learning_preferences')
                        )
                        
                        # Create download
                        st.download_button(
                            "⬇️ Download HTML Report",
                            data=report_html,
                            file_name=f"learning_path_report_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                            mime="text/html",
                            help="Download interactive HTML report"
                        )
                        
                        st.success("🎉 Dynamic report generated successfully!")
                        
                    except Exception as e:
                        st.error(f"Error generating report: {str(e)}")
                        # Fallback to JSON download
                        st.download_button(
                            "⬇️ Download JSON (Fallback)",
                            data=json.dumps(st.session_state.learning_path, indent=2),
                            file_name=f"learning_path_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                            mime="application/json"
                        )
        
        with col_4:
            if st.button("🗑️ Clear Learning Path", help="Remove current learning path"):
                # Clear from both session state and database
                st.session_state.learning_path = None
                if current_employee_id:
                    sync_employee_learning_path(current_employee_id, None)
                    # Clear selections and progress
                    if current_employee_id in st.session_state.selected_courses_for_plan:
                        st.session_state.selected_courses_for_plan[current_employee_id] = {}
                    if current_employee_id in st.session_state.learning_path_progress:
                        st.session_state.learning_path_progress[current_employee_id] = {}
                
                st.success("Learning path cleared!")
                st.rerun()
    
    else:
        # No learning path exists - show suggestions (existing functionality)
        st.markdown("### 💡 Try These Smart Commands")
        
        sample_commands = [
            ("🐍 Python Learning", "I want to learn Python in 3 weeks"),
            ("🔍 Search Trends", "Search for latest AI trends 2024"),
            ("📊 Data Science Path", "I have 5 weeks to prepare for data scientist role"),
            ("🎓 Udemy Courses", "Find Udemy courses for machine learning"),
            ("⚡ Quick Plan", "Create a quick 1-week intensive plan"),
            ("🔗 Leadership Skills", "I need to learn leadership skills urgently")
        ]
        
        st.markdown("**Smart Examples:**")
        for i, (icon_text, command) in enumerate(sample_commands):
            if st.button(f"{icon_text}", key=f"cmd_{i}", help=command):
                process_enhanced_user_input(command)
# Add employee profile synchronization function

# First, add these helper functions to your code:

def sync_employee_profile_changes(employee_id, updated_profile):
    """Sync any changes made to employee profile back to the database"""
    if employee_id and employee_id in st.session_state.employee_database:
        # Get current database entry
        db_entry = st.session_state.employee_database[employee_id]
        
        # Preserve manager-specific fields that shouldn't be changed by employee
        preserved_fields = ['manager_id', 'employee_id', 'department'] # Added department to preserved fields
        
        for field in preserved_fields:
            if field in db_entry:
                updated_profile[field] = db_entry[field]
        
        # Update database
        st.session_state.employee_database[employee_id].update(updated_profile)
        
        # Also update session state employee profile if it exists and matches the current employee
        if 'employee_profile' in st.session_state and st.session_state.employee_profile.get('employee_id') == employee_id:
            st.session_state.employee_profile.update(updated_profile)
        
        return True
    return False
# Enhanced employee profile editing with sync

def enhanced_employee_profile_editing():
    """Enhanced employee profile editing for the Employee Portal with database synchronization"""
    
    st.markdown("### 👤 Edit Your Profile")
    
    # Show current employee info
    current_employee_id = get_current_employee_id()
    if current_employee_id:
        st.info(f"Employee ID: {current_employee_id}")
        
        # Get current employee data
        if current_employee_id in st.session_state.employee_database:
            employee_data = st.session_state.employee_database[current_employee_id]
        else:
            employee_data = st.session_state.get('employee_profile', {})
    else:
        st.warning("No employee profile found. Please ensure you're logged in correctly.")
        return
    
    # Profile editing form
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Basic Information")
        
        name = st.text_input("Name", value=employee_data.get("name", ""), key="emp_name")
        
        current_role = st.selectbox(
            "Current Role", 
            options=list(role_requirements.keys()), 
            index=list(role_requirements.keys()).index(employee_data.get("current_role", list(role_requirements.keys())[0])) 
            if employee_data.get("current_role") in role_requirements else 0,
            key="emp_role"
        )
        
        experience_level = st.selectbox(
            "Experience Level",
            ["Entry Level", "Junior", "Mid-level", "Senior", "Expert"],
            index=["Entry Level", "Junior", "Mid-level", "Senior", "Expert"].index(
                employee_data.get("experience_level", "Mid-level")
            ),
            key="emp_exp"
        )
    
    with col2:
        st.markdown("#### Skills & Proficiency")
        
        # Get all available skills from role requirements
        all_skills = set()
        for role_data in role_requirements.values():
            all_skills.update(role_data["required_skills"].keys())
            all_skills.update(role_data["preferred_skills"].keys())
        
        skills = st.multiselect(
            "Current Skills", 
            options=sorted(list(all_skills)), 
            default=list(employee_data.get("skill_proficiency", {}).keys()), # Use keys from skill_proficiency
            key="emp_skills"
        )
        
        # Skill proficiency levels
        proficiency_levels = ["Beginner", "Intermediate", "Advanced", "Expert"]
        skill_proficiency = {}
        if skills:
            st.markdown("**Skill Proficiency Levels:**")
            for skill in skills:
                current_proficiency = employee_data.get("skill_proficiency", {}).get(skill, "Beginner")
                
                # Ensure the current_proficiency is in the list before finding index
                if current_proficiency not in proficiency_levels:
                    current_proficiency = "Beginner" # Fallback if proficiency is invalid
                
                proficiency = st.selectbox(
                    f"Proficiency in {skill}",
                    proficiency_levels,
                    index=proficiency_levels.index(current_proficiency),
                    key=f"emp_prof_{skill}"
                )
                skill_proficiency[skill] = proficiency
    
    # Career goals and completed courses
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("#### Career Goals")
        career_goals = st.multiselect(
            "Career Aspirations", 
            options=list(role_requirements.keys()), 
            default=employee_data.get("career_goals", []),
            key="emp_goals"
        )
    
    with col4:
        st.markdown("#### Completed Courses")
        all_courses = course_catalog["title"].tolist()
        completed_courses = st.multiselect(
            "Completed Courses", 
            options=all_courses,
            default=employee_data.get("completed_courses", []),
            key="emp_courses"
        )
    
    # Save button with enhanced sync
    col_save, col_cancel = st.columns(2)
    
    with col_save:
        if st.button("💾 Save Profile Changes", type="primary", key="save_profile"):
            updated_profile = {
                "name": name,
                "current_role": current_role,
                "skills": list(skill_proficiency.keys()), # Update skills list based on proficiency keys
                "skill_proficiency": skill_proficiency,
                "completed_courses": completed_courses,
                "career_goals": career_goals,
                "experience_level": experience_level
            }
            
            # Sync changes
            if sync_employee_profile_changes(current_employee_id, updated_profile):
                st.success("✅ Profile changes saved and synchronized!")
                
                # Update current session profile
                st.session_state.employee_profile.update(updated_profile)
                
                # Ask if they want to regenerate learning path
                if st.session_state.get('learning_path'):
                    st.info("💡 Profile updated! Would you like to regenerate your learning path to reflect these changes?")
                
                st.rerun()
            else:
                st.error("Failed to save profile changes.")
    
    with col_cancel:
        if st.button("🔄 Reset Changes", key="reset_profile"):
            st.rerun()


# Set up Google Gemini API
def initialize_gemini_api():
    api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        st.error("Gemini API key not found. Please set it in Streamlit secrets or as an environment variable.")
        st.stop()
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash')

gemini_model = initialize_gemini_api()

# AI-powered DuckDuckGo Search Agent
@dataclass
class UdemyCourse:
    title: str
    url: str
    description: str
    rating: float
    price: str
    duration: str
    level: str
    id: str = None # Add ID for tracking

class AISearchAgent:
    def __init__(self):
        self.base_url = "[https://html.duckduckgo.com/html](https://html.duckduckgo.com/html)"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def search_web(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search DuckDuckGo for web results"""
        try:
            # Modified params to use HTML API instead of JSON API
            params = {
                'q': query,
                'kl': 'us-en',  # Region and language
                's': '0',       # Offset
                'dc': '0'       # Start position
            }
            
            response = self.session.get(self.base_url, params=params, timeout=10, verify=False)
            response.raise_for_status()
            
            # Since we're using HTML API, we'll parse the response text
            html_content = response.text
            
            results = []
            # Use regex to extract results from HTML
            result_pattern = r'<h2 class="result__title">.*?<a href="([^"]+)".*?>([^<]+)</a>.*?<a class="result__snippet"[^>]*>([^<]+)</a>'
            matches = re.findall(result_pattern, html_content, re.DOTALL)
            
            for url, title, snippet in matches[:max_results]:
                # Clean up the extracted data
                clean_url = url.replace('&amp;', '&')
                clean_title = re.sub(r'\s+', ' ', title).strip()
                clean_snippet = re.sub(r'\s+', ' ', snippet).strip()
                
                results.append({
                    'title': clean_title,
                    'url': clean_url,
                    'snippet': clean_snippet
                })
            
            return results
            
        except Exception as e:
            print(f"Search error: {str(e)}")
            return []

    def search_udemy_courses(self, skill: str,current_role:str, max_results: int = 10) -> List[Dict]:
        """Search specifically for Udemy courses using DuckDuckGo"""
        try:
            # Search for Udemy courses specifically
            query = f"site:udemy.com {skill} top course for {current_role}"
            print(query)
            # Use DuckDuckGo HTML search since JSON API is limited
            search_url = f"[https://html.duckduckgo.com/html/](https://html.duckduckgo.com/html/)"
            params = {
                'q': query,
                'kl': 'us-en'
            }
            
            response = self.session.get(search_url, params=params, timeout=15,verify=False)
            response.raise_for_status()
            
            # Parse HTML results (basic extraction)
            html_content = response.text
            print(html_content)
            results = []
            
            # Extract Udemy course URLs using regex
            udemy_pattern = r'href="([^"]*udemy\.com/course/[^"]*)"[^>]*>([^<]+)</a>'
            matches = re.findall(udemy_pattern, html_content)
            
            for url, title in matches[:max_results]:
                # Clean up the URL and title
                clean_url = url.replace('&amp;', '&')
                if not clean_url.startswith('http'):
                    clean_url = 'https://' + clean_url.lstrip('//')
                
                clean_title = re.sub(r'<[^>]+>', '', title).strip()
                
                if '[udemy.com/course/](https://udemy.com/course/)' in clean_url and clean_title:
                    results.append({
                        'title': clean_title,
                        'url': clean_url,
                        'snippet': f"Udemy course: {clean_title}"
                    })
            
            # If no results from HTML parsing, try alternative search
            if not results:
                results = self._alternative_udemy_search(skill, max_results)
            
            return results
            
        except Exception as e:
            print(f"Udemy search error: {e}")
            return self._alternative_udemy_search(skill, max_results)
    
    def _alternative_udemy_search(self, skill: str, max_results: int = 5) -> List[Dict]:
        """Alternative method to find Udemy courses"""
        try:
            # Try with JSON API but filter for Udemy
            params = {
                'q': f"udemy {skill} course",
                'format': 'json',
                'no_redirect': '1',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = self.session.get(self.base_url, params=params, timeout=10, verify=False)
            response.raise_for_status()
            
            data = response.json()
            print(data)
            results = []
            
            # Check related topics for Udemy links
            if 'RelatedTopics' in data:
                for topic in data['RelatedTopics']:
                    if isinstance(topic, dict) and 'FirstURL' in topic:
                        url = topic.get('FirstURL', '')
                        if 'udemy.com' in url:
                            results.append({
                                'title': topic.get('Text', '').split(' - ')[0] if ' - ' in topic.get('Text', '') else topic.get('Text', ''),
                                'url': url,
                                'snippet': topic.get('Text', '')
                            })
            
            return results[:max_results]
            
        except Exception as e:
            print(f"Alternative search error: {e}")
            return []

    def search_learning_resources(self, skill: str) -> Dict:
        """Search for learning resources for a specific skill"""
        queries = [
            f"{skill} online course tutorial",
            f"learn {skill} programming",
            f"{skill} certification training"
        ]
        
        all_results = []
        for query in queries:
            results = self.search_web(query, max_results=3)
            all_results.extend(results)
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                unique_results.append(result)
        
        return {
            'skill': skill,
            'resources': unique_results[:8],  # Limit to top 8 results
            'search_summary': f"Found {len(unique_results)} learning resources for {skill}"
        }

# Enhanced Udemy Course Search Agent
class UdemyCourseAgent:
    def __init__(self):
        self.base_url = "[https://www.udemy.com](https://www.udemy.com)"
        self.search_agent = AISearchAgent()
    
    def generate_udemy_courses(self, skills: List[str],current_role:str) -> List[UdemyCourse]:
        """Find real Udemy courses using web search"""
        if not skills:
            return []
        
        all_courses = []
        
        for skill in skills:
            # Search for real Udemy courses
            search_results = self.search_agent.search_udemy_courses(skill,current_role, max_results=2)
            
            for result in search_results:
                # Extract course info and enhance with realistic details
                course = self._create_course_from_search_result(result, skill)
                if course:
                    all_courses.append(course)
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        
        # If we found real courses, return them
        if all_courses:
            return all_courses
        
        # Fallback: Generate realistic courses with proper Udemy URL structure
        return self._generate_fallback_courses(skills)
    
    def _create_course_from_search_result(self, result: Dict, skill: str) -> UdemyCourse:
        """Create a UdemyCourse object from search result with enhanced details"""
        try:
            title = result.get('title', '')
            url = result.get('url', '')
            
            # Validate URL
            if not url or '[udemy.com/course/](https://udemy.com/course/)' not in url:
                return None
            
            # Generate realistic course details using AI or heuristics
            course_details = self._enhance_course_details(title, skill)
            
            return UdemyCourse(
                title=title,
                url=url,
                description=course_details['description'],
                rating=course_details['rating'],
                price=course_details['price'],
                duration=course_details['duration'],
                level=course_details['level'],
                id=f"udemy_{str(uuid.uuid4())}" # Assign a unique ID
            )
            
        except Exception as e:
            print(f"Error creating course from result: {e}")
            return None
    
    def _enhance_course_details(self, title: str, skill: str) -> Dict:
        """Generate realistic course details based on title and skill"""
        # Realistic course details based on common patterns
        import random
        
        # Generate description based on title and skill
        description_templates = [
            f"Master {skill} with hands-on projects and real-world examples. Perfect for beginners and professionals looking to advance their skills.",
            f"Complete {skill} course covering fundamentals to advanced concepts. Build practical projects and gain industry-relevant skills.",
            f"Learn {skill} from scratch with step-by-step guidance. Includes exercises, quizzes, and practical assignments.",
            f"Comprehensive {skill} training with expert instruction. Gain confidence through practical application and real-world scenarios.",
            f"Practical {skill} course designed for modern developers. Learn best practices and industry standards."
        ]
        
        # Realistic ratings (Udemy courses typically range 4.0-4.8)
        ratings = [4.0, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8]
        
        # Realistic prices
        prices = ["$19.99", "$29.99", "$49.99", "$69.99", "$89.99", "$99.99"]
        
        # Realistic durations
        durations = ["3 hours", "5 hours", "8 hours", "12 hours", "15 hours", "20 hours", "25 hours"]
        
        # Determine level based on title keywords
        title_lower = title.lower()
        if any(word in title_lower for word in ['beginner', 'basics', 'introduction', 'getting started']):
            level = "Beginner"
        elif any(word in title_lower for word in ['advanced', 'expert', 'mastery', 'professional']):
            level = "Advanced"
        else:
            level = "Intermediate"
        
        return {
            'description': random.choice(description_templates),
            'rating': random.choice(ratings),
            'price': random.choice(prices),
            'duration': random.choice(durations),
            'level': level
        }
    
    def _generate_fallback_courses(self, skills: List[str]) -> List[UdemyCourse]:
        """Generate fallback courses with realistic Udemy URL structure"""
        courses = []
        skills_text = ', '.join(skills)
        
        # Common Udemy course URL patterns for different skills
        course_templates = [
            {
                'title_template': "Complete {skill} Bootcamp",
                'url_template': "complete-{skill}-bootcamp-zero-to-mastery",
                'description': "Master {skill} from beginner to advanced level with hands-on projects and real-world applications.",
                'level': "All Levels"
            },
            {
                'title_template': "{skill} for Beginners",
                'url_template': "{skill}-for-beginners-complete-course",
                'description': "Learn {skill} from scratch with step-by-step guidance and practical exercises.",
                'level': "Beginner"
            },
            {
                'title_template': "Advanced {skill} Masterclass",
                'url_template': "advanced-{skill}-masterclass-expert-level",
                'description': "Take your {skill} skills to the next level with advanced techniques and best practices.",
                'level': "Advanced"
            },
            {
                'title_template': "{skill} Projects Course",
                'url_template': "{skill}-projects-practical-hands-on-course",
                'description': "Build real-world {skill} projects and strengthen your portfolio with practical experience.",
                'level': "Intermediate"
            },
            {
                'title_template': "Professional {skill} Development",
                'url_template': "professional-{skill}-development-course",
                'description': "Professional-grade {skill} training designed for career advancement and industry success.",
                'level': "Intermediate"
            }
        ]
        
        for i, skill in enumerate(skills[:5]):
            template = course_templates[i % len(course_templates)]
            
            # Clean skill name for URL
            clean_skill = re.sub(r'[^a-zA-Z0-9]', '-', skill.lower()).strip('-')
            
            course = UdemyCourse(
                title=template['title_template'].format(skill=skill),
                url=f"[https://www.udemy.com/course/](https://www.udemy.com/course/){template['url_template'].format(skill=clean_skill)}/",
                description=template['description'].format(skill=skill),
                rating=round(4.0 + (i * 0.15), 1),  # Vary ratings from 4.0 to 4.6
                price=["$49.99", "$69.99", "$89.99", "$59.99", "$79.99"][i],
                duration=["12 hours", "18 hours", "25 hours", "15 hours", "20 hours"][i],
                level=template['level'],
                id=f"udemy_{str(uuid.uuid4())}" # Assign a unique ID
            )
            courses.append(course)
        
        return courses

# Initialize agents
search_agent = AISearchAgent()
udemy_agent = UdemyCourseAgent()

# Enhanced course catalog with duration parsing
@st.cache_data
def load_enhanced_course_catalog():
    return pd.DataFrame([
        {"id": "COURSE001", "title": "Python Programming Essentials", "type": "Course", "duration": "4 weeks", "duration_weeks": 4,
         "skills": ["Python", "Programming"], "difficulty": "Beginner", "learning_style": "Hands-on",
         "description": "Learn Python programming fundamentals with practical exercises"},
        {"id": "COURSE002", "title": "Machine Learning Fundamentals", "type": "Course", "duration": "6 weeks", "duration_weeks": 6,
         "skills": ["Machine Learning", "Python", "Statistics"], "difficulty": "Intermediate", "learning_style": "Mixed",
         "description": "Introduction to machine learning algorithms and applications"},
        {"id": "COURSE003", "title": "Data Leadership Workshop", "type": "Workshop", "duration": "2 days", "duration_weeks": 0.5,
         "skills": ["Leadership", "Management", "Data Strategy"], "difficulty": "Advanced", "learning_style": "Interactive",
         "description": "Leadership skills for data professionals"},
        {"id": "COURSE004", "title": "Advanced SQL for Data Analysis", "type": "Course", "duration": "3 weeks", "duration_weeks": 3,
         "skills": ["SQL", "Database", "Data Analysis"], "difficulty": "Intermediate", "learning_style": "Hands-on",
         "description": "Advanced SQL techniques for complex data analysis"},
        {"id": "COURSE005", "title": "Data Visualization with Tableau", "type": "Course", "duration": "2 weeks", "duration_weeks": 2,
         "skills": ["Data Visualization", "Tableau"], "difficulty": "Beginner", "learning_style": "Visual",
         "description": "Create impactful data visualizations using Tableau"},
        {"id": "COURSE006", "title": "Statistics for Data Science", "type": "Course", "duration": "5 weeks", "duration_weeks": 5,
         "skills": ["Statistics", "Data Science"], "difficulty": "Intermediate", "learning_style": "Mixed",
         "description": "Statistical methods essential for data science"},
        {"id": "COURSE007", "title": "Deep Learning Specialization", "type": "Course", "duration": "12 weeks", "duration_weeks": 12,
         "skills": ["Deep Learning", "Neural Networks", "Python"], "difficulty": "Advanced", "learning_style": "Hands-on",
         "description": "Comprehensive deep learning techniques and applications"},
        {"id": "COURSE008", "title": "Agile Project Management", "type": "Course", "duration": "3 weeks", "duration_weeks": 3,
         "skills": ["Project Management", "Agile"], "difficulty": "Beginner", "learning_style": "Interactive",
         "description": "Agile methodologies for project management"},
        {"id": "COURSE009", "title": "Quick Data Analysis Bootcamp", "type": "Intensive", "duration": "1 week", "duration_weeks": 1,
         "skills": ["Data Analysis", "Statistics"], "difficulty": "Intermediate", "learning_style": "Intensive",
         "description": "Rapid introduction to data analysis techniques"},
        {"id": "COURSE010", "title": "Python for Data Science - Fast Track", "type": "Bootcamp", "duration": "2 weeks", "duration_weeks": 2,
         "skills": ["Python", "Data Science"], "difficulty": "Intermediate", "learning_style": "Intensive",
         "description": "Accelerated Python course for data science applications"},
        {"id": "COURSE011", "title": "Business Intelligence Essentials", "type": "Course", "duration": "4 weeks", "duration_weeks": 4,
         "skills": ["Business Intelligence", "Data Analysis"], "difficulty": "Beginner", "learning_style": "Mixed",
         "description": "Introduction to BI tools and methodologies"},
        {"id": "COURSE012", "title": "Cloud Computing Fundamentals", "type": "Course", "duration": "3 weeks", "duration_weeks": 3,
         "skills": ["Cloud Computing", "AWS"], "difficulty": "Beginner", "learning_style": "Hands-on",
         "description": "Learn cloud computing basics with AWS"},
        {"id": "COURSE013", "title": "Data Analysis Fundamentals", "type": "Course", "duration": "3 weeks", "duration_weeks": 3,
         "skills": ["Data Analysis", "Statistics"], "difficulty": "Beginner", "learning_style": "Hands-on",
         "description": "Learn Data Analysis basics"},
        {"id": "COURSE014", "title": "Excel Advanced", "type": "Course", "duration": "3 weeks", "duration_weeks": 3,
         "skills": ["Data Analysis", "Excel"], "difficulty": "Intermediate", "learning_style": "Hands-on",
         "description": "Learn Excel"},
        {"id": "COURSE015", "title": "Object-Oriented Programming", "type": "Course", "duration": "3 weeks", "duration_weeks": 3,
         "skills": ["Python", "Java", "Programming"], "difficulty": "Intermediate", "learning_style": "Hands-on",
         "description": "Learn object-oriented programming concepts"},
        {"id": "COURSE016", "title": "SQL Intermediate", "type": "Course", "duration": "2 weeks", "duration_weeks": 2,
         "skills": ["SQL", "Database"], "difficulty": "Intermediate", "learning_style": "Hands-on",
         "description": "Intermediate SQL techniques and database management"},
        {"id": "COURSE017", "title": "Python Basics", "type": "Course", "duration": "3 weeks", "duration_weeks": 3,
         "skills": ["Python", "Programming"], "difficulty": "Beginner", "learning_style": "Hands-on",
         "description": "Introduction to Python programming language"},
        {"id": "COURSE018", "title": "Business Analysis Fundamentals", "type": "Course", "duration": "4 weeks", "duration_weeks": 4,
         "skills": ["Business Analysis", "Requirements Gathering"], "difficulty": "Beginner", "learning_style": "Mixed",
         "description": "Learn business analysis principles and techniques"},
        {"id": "COURSE019", "title": "SQL Basics", "type": "Course", "duration": "2 weeks", "duration_weeks": 2,
         "skills": ["SQL", "Database"], "difficulty": "Beginner", "learning_style": "Hands-on",
         "description": "Introduction to SQL and database basics"},
        {"id": "COURSE020", "title": "Database Design", "type": "Course", "duration": "3 weeks", "duration_weeks": 3,
         "skills": ["Database", "SQL", "Data Modeling"], "difficulty": "Intermediate", "learning_style": "Mixed",
         "description": "Learn database design principles and normalization"},
        {"id": "COURSE021", "title": "Statistical Analysis", "type": "Course", "duration": "4 weeks", "duration_weeks": 4,
         "skills": ["Statistics", "Data Analysis"], "difficulty": "Intermediate", "learning_style": "Mixed",
         "description": "Statistical methods for data analysis and interpretation"},
        {"id": "COURSE022", "title": "Deep Learning Basics", "type": "Course", "duration": "6 weeks", "duration_weeks": 6,
         "skills": ["Deep Learning", "Neural Networks", "Python"], "difficulty": "Intermediate", "learning_style": "Hands-on",
         "description": "Introduction to deep learning and neural networks"},
        {"id": "COURSE023", "title": "Programming Fundamentals", "type": "Course", "duration": "4 weeks", "duration_weeks": 4,
         "skills": ["Programming", "Problem Solving"], "difficulty": "Beginner", "learning_style": "Hands-on",
         "description": "Basic programming concepts and problem-solving techniques"},
        {"id": "COURSE024", "title": "Version Control", "type": "Course", "duration": "1 week", "duration_weeks": 1,
         "skills": ["Git", "Version Control"], "difficulty": "Beginner", "learning_style": "Hands-on",
         "description": "Learn Git and version control best practices"},
        {"id": "COURSE025", "title": "Linux Administration", "type": "Course", "duration": "3 weeks", "duration_weeks": 3,
         "skills": ["Linux", "System Administration"], "difficulty": "Intermediate", "learning_style": "Hands-on",
         "description": "Linux system administration and command line"},
        {"id": "COURSE026", "title": "Docker Essentials", "type": "Course", "duration": "2 weeks", "duration_weeks": 2,
         "skills": ["Docker", "Containerization"], "difficulty": "Intermediate", "learning_style": "Hands-on",
         "description": "Docker containerization fundamentals"},
        {"id": "COURSE027", "title": "AWS Fundamentals", "type": "Course", "duration": "3 weeks", "duration_weeks": 3,
         "skills": ["AWS", "Cloud Computing"], "difficulty": "Beginner", "learning_style": "Mixed",
         "description": "Introduction to Amazon Web Services"},
        {"id": "COURSE028", "title": "Web Development Fundamentals", "type": "Course", "duration": "4 weeks", "duration_weeks": 4,
         "skills": ["HTML", "CSS", "JavaScript", "Web Development"], "difficulty": "Beginner", "learning_style": "Hands-on",
         "description": "Basic web development with HTML, CSS, and JavaScript"},
        {"id": "COURSE029", "title": "React Basics", "type": "Course", "duration": "3 weeks", "duration_weeks": 3,
         "skills": ["React", "JavaScript", "Frontend"], "difficulty": "Intermediate", "learning_style": "Hands-on",
         "description": "Introduction to React framework"},
        {"id": "COURSE030", "title": "Data Engineering Fundamentals", "type": "Course", "duration": "5 weeks", "duration_weeks": 5,
         "skills": ["Data Engineering", "ETL", "Python"], "difficulty": "Intermediate", "learning_style": "Mixed",
         "description": "Introduction to data engineering and ETL processes"},
        {"id": "COURSE031", "title": "Big Data Processing", "type": "Course", "duration": "4 weeks", "duration_weeks": 4,
         "skills": ["Big Data", "Apache Spark", "Data Processing"], "difficulty": "Advanced", "learning_style": "Hands-on",
         "description": "Processing large datasets with Apache Spark"},
        {"id": "COURSE032", "title": "Software Testing Fundamentals", "type": "Course", "duration": "3 weeks", "duration_weeks": 3,
         "skills": ["Testing", "Quality Assurance"], "difficulty": "Beginner", "learning_style": "Mixed",
         "description": "Software testing principles and methodologies"},
        {"id": "COURSE033", "title": "Test Automation", "type": "Course", "duration": "4 weeks", "duration_weeks": 4,
         "skills": ["Test Automation", "Selenium", "Testing"], "difficulty": "Intermediate", "learning_style": "Hands-on",
         "description": "Automated testing with Selenium and other tools"},
        {"id": "COURSE034", "title": "Advanced Machine Learning", "type": "Course", "duration": "8 weeks", "duration_weeks": 8,
         "skills": ["Machine Learning", "Advanced Analytics", "Python"], "difficulty": "Advanced", "learning_style": "Mixed",
         "description": "Advanced machine learning algorithms and techniques"},
        {"id": "COURSE035", "title": "MLOps Pipeline", "type": "Course", "duration": "6 weeks", "duration_weeks": 6,
         "skills": ["MLOps", "Machine Learning", "DevOps"], "difficulty": "Advanced", "learning_style": "Hands-on",
         "description": "Machine learning operations and deployment pipelines"},
        {"id": "COURSE036", "title": "System Design Mastery", "type": "Course", "duration": "6 weeks", "duration_weeks": 6,
         "skills": ["System Design", "Architecture", "Scalability"], "difficulty": "Advanced", "learning_style": "Mixed",
         "description": "Large-scale system design and architecture"},
        {"id": "COURSE037", "title": "Cloud Architecture", "type": "Course", "duration": "5 weeks", "duration_weeks": 5,
         "skills": ["Cloud Architecture", "AWS", "System Design"], "difficulty": "Advanced", "learning_style": "Mixed",
         "description": "Design and implement cloud-based architectures"},
        {"id": "COURSE038", "title": "Leadership Essentials", "type": "Course", "duration": "3 weeks", "duration_weeks": 3,
         "skills": ["Leadership", "Team Management", "Communication"], "difficulty": "Intermediate", "learning_style": "Interactive",
         "description": "Essential leadership skills for technical professionals"}
    ])

course_catalog = load_enhanced_course_catalog()

# Enhanced role requirements with skill proficiency levels
@st.cache_data
def load_enhanced_role_requirements():
    return {
        # Data & Analytics Roles
        "Junior Data Analyst": {
            "required_skills": {"Excel": "Intermediate", "SQL": "Beginner", "Data Visualization": "Beginner", "Statistics": "Beginner"},
            "preferred_skills": {"Python": "Beginner", "Tableau": "Beginner", "Power BI": "Beginner"},
            "experience_level": "Entry"
        },
        "Data Analyst": {
            "required_skills": {"SQL": "Intermediate", "Data Visualization": "Intermediate", "Excel": "Advanced", "Statistics": "Intermediate", "Python": "Intermediate"},
            "preferred_skills": {"R": "Beginner", "Tableau": "Intermediate", "Power BI": "Intermediate", "Database Management": "Intermediate", "Business Intelligence": "Intermediate"},
            "experience_level": "Entry to Mid"
        },
        "Senior Data Analyst": {
            "required_skills": {"SQL": "Advanced", "Python": "Advanced", "Data Visualization": "Advanced", "Statistics": "Advanced", "Business Intelligence": "Advanced"},
            "preferred_skills": {"R": "Intermediate", "Advanced Analytics": "Intermediate", "Machine Learning": "Beginner", "Cloud Platforms": "Beginner", "Leadership": "Beginner"},
            "experience_level": "Mid to Senior"
        },
        "Data Scientist": {
            "required_skills": {"Python": "Advanced", "Machine Learning": "Intermediate", "Statistics": "Advanced", "Data Visualization": "Intermediate", "SQL": "Intermediate"},
            "preferred_skills": {"R": "Intermediate", "Deep Learning": "Beginner", "Big Data": "Beginner", "Cloud Computing": "Beginner", "A/B Testing": "Intermediate"},
            "experience_level": "Mid to Senior"
        },
        "Senior Data Scientist": {
            "required_skills": {"Python": "Expert", "Machine Learning": "Advanced", "Deep Learning": "Intermediate", "Statistics": "Expert", "Big Data": "Intermediate"},
            "preferred_skills": {"MLOps": "Intermediate", "Research": "Intermediate", "Model Deployment": "Intermediate", "Cloud Architecture": "Beginner", "Mentoring": "Intermediate"},
            "experience_level": "Senior"
        },
        "Principal Data Scientist": {
            "required_skills": {"Machine Learning": "Expert", "Deep Learning": "Advanced", "Research": "Advanced", "Leadership": "Advanced", "Strategy": "Advanced"},
            "preferred_skills": {"Publications": "Advanced", "Patent Development": "Advanced", "Cross-functional Collaboration": "Advanced", "Technical Vision": "Expert"},
            "experience_level": "Senior to Executive"
        },
        "ML Engineer": {
            "required_skills": {"Python": "Advanced", "Machine Learning": "Intermediate", "MLOps": "Beginner", "DevOps": "Beginner", "Cloud Computing": "Beginner"},
            "preferred_skills": {"Kubernetes": "Beginner", "Docker": "Intermediate", "Model Deployment": "Intermediate", "CI/CD": "Intermediate", "Monitoring": "Intermediate"},
            "experience_level": "Mid to Senior"
        },
        "Senior ML Engineer": {
            "required_skills": {"MLOps": "Advanced", "Machine Learning": "Advanced", "System Design": "Intermediate", "Cloud Architecture": "Intermediate", "DevOps": "Intermediate"},
            "preferred_skills": {"Kubernetes": "Intermediate", "Docker": "Intermediate", "Model Deployment": "Intermediate", "CI/CD": "Intermediate", "Monitoring": "Intermediate", "Platform Engineering": "Intermediate", "Model Optimization": "Advanced", "Infrastructure": "Intermediate", "Team Leadership": "Intermediate"},
            "experience_level": "Senior"
        },
        "AI Specialist": {
            "required_skills": {"Machine Learning": "Advanced", "Deep Learning": "Advanced", "Python": "Expert", "Mathematics": "Advanced", "Neural Networks": "Advanced"},
            "preferred_skills": {"Computer Vision": "Intermediate", "NLP": "Intermediate", "Research": "Advanced", "Publications": "Intermediate", "Algorithm Development": "Advanced"},
            "experience_level": "Senior"
        },
        "Data Science Manager": {
            "required_skills": {"Leadership": "Advanced", "Data Science": "Advanced", "Team Management": "Advanced", "Strategy": "Advanced", "Communication": "Advanced"},
            "preferred_skills": {"Project Management": "Advanced", "Business Intelligence": "Advanced", "Stakeholder Management": "Advanced", "Budget Planning": "Advanced"},
            "experience_level": "Senior to Executive"
        },
        
        # Engineering Roles
        "Junior Software Engineer": {
            "required_skills": {"Python": "Intermediate", "Data Structures": "Beginner", "Algorithms": "Beginner", "Git": "Intermediate"},
            "preferred_skills": {"Java": "Beginner", "Database": "Beginner", "Web Development": "Beginner", "Testing": "Beginner"},
            "experience_level": "Entry"
        },
        "Software Engineer": {
            "required_skills": {"Python": "Advanced", "Java": "Intermediate", "Data Structures": "Intermediate", "Algorithms": "Intermediate", "Database": "Intermediate"},
            "preferred_skills": {"Cloud Computing": "Beginner", "DevOps": "Beginner", "System Design": "Beginner", "API Development": "Intermediate"},
            "experience_level": "Entry to Mid"
        },
        "Senior Software Engineer": {
            "required_skills": {"Python": "Expert", "Java": "Advanced", "System Design": "Intermediate", "Database": "Advanced", "API Development": "Advanced"},
            "preferred_skills": {"Cloud Architecture": "Intermediate", "DevOps": "Intermediate", "Microservices": "Intermediate", "Performance Optimization": "Advanced", "Mentoring": "Intermediate"},
            "experience_level": "Mid to Senior"
        },
        "Tech Lead": {
            "required_skills": {"System Design": "Advanced", "Leadership": "Advanced", "Architecture": "Advanced", "Code Review": "Advanced", "Project Management": "Advanced"},
            "preferred_skills": {"Cross-team Collaboration": "Advanced", "Technical Strategy": "Advanced", "Mentoring": "Advanced", "Agile Methodologies": "Advanced"},
            "experience_level": "Senior"
        },
        "Principal Engineer": {
            "required_skills": {"System Architecture": "Expert", "Technical Leadership": "Expert", "Strategy": "Advanced", "Cross-functional Collaboration": "Advanced"},
            "preferred_skills": {"Innovation": "Advanced", "Technical Vision": "Expert", "Research": "Advanced", "Industry Expertise": "Expert"},
            "experience_level": "Senior to Executive"
        },
        "DevOps Engineer": {
            "required_skills": {"Linux": "Intermediate", "Docker": "Intermediate", "Kubernetes": "Beginner", "CI/CD": "Intermediate", "Cloud Platforms": "Intermediate"},
            "preferred_skills": {"Infrastructure as Code": "Intermediate", "Monitoring": "Intermediate", "Security": "Beginner", "Automation": "Intermediate"},
            "experience_level": "Mid"
        },
        "Senior DevOps Engineer": {
            "required_skills": {"Kubernetes": "Advanced", "Cloud Architecture": "Intermediate", "Infrastructure as Code": "Advanced", "Security": "Intermediate", "Monitoring": "Advanced"},
            "preferred_skills": {"Cost Optimization": "Intermediate", "Disaster Recovery": "Intermediate", "Team Leadership": "Intermediate", "Platform Engineering": "Intermediate"},
            "experience_level": "Senior"
        },
        "Cloud Architect": {
            "required_skills": {"Cloud Platforms": "Advanced", "System Architecture": "Advanced", "Security": "Advanced", "Cost Optimization": "Intermediate"},
            "preferred_skills": {"Multi-cloud": "Intermediate", "Enterprise Architecture": "Advanced", "Compliance": "Advanced", "Strategy": "Advanced"},
            "experience_level": "Senior to Executive"
        },
        
        # Product & Business Roles
        "Business Analyst": {
            "required_skills": {"Excel": "Advanced", "Data Analysis": "Intermediate", "Requirements Gathering": "Intermediate", "Communication": "Intermediate"},
            "preferred_skills": {"SQL": "Beginner", "Process Mapping": "Intermediate", "Stakeholder Management": "Intermediate", "Documentation": "Advanced"},
            "experience_level": "Entry to Mid"
        },
        "Senior Business Analyst": {
            "required_skills": {"SQL": "Intermediate", "Data Analysis": "Advanced", "Process Optimization": "Advanced", "Stakeholder Management": "Advanced"},
            "preferred_skills": {"Python": "Beginner", "Business Intelligence": "Intermediate", "Project Management": "Intermediate", "Strategy": "Intermediate"},
            "experience_level": "Mid to Senior"
        },
        "Product Manager": {
            "required_skills": {"Product Strategy": "Intermediate", "Market Research": "Intermediate", "Stakeholder Management": "Intermediate", "Analytics": "Intermediate"},
            "preferred_skills": {"Technical Background": "Beginner", "A/B Testing": "Intermediate", "User Research": "Intermediate", "Roadmap Planning": "Intermediate"},
            "experience_level": "Mid to Senior"
        },
        "Senior Product Manager": {
            "required_skills": {"Product Strategy": "Advanced", "Leadership": "Intermediate", "Cross-functional Collaboration": "Advanced", "Market Analysis": "Advanced"},
            "preferred_skills": {"Technical Depth": "Intermediate", "Competitive Analysis": "Advanced", "Go-to-Market": "Advanced", "Team Management": "Advanced"},
            "experience_level": "Senior"
        },
        
        # Specialized Technical Roles
        "Data Engineer": {
            "required_skills": {"Python": "Advanced", "SQL": "Advanced", "ETL": "Intermediate", "Data Pipelines": "Intermediate", "Database": "Intermediate"},
            "preferred_skills": {"Big Data": "Beginner", "Cloud Platforms": "Beginner", "Apache Spark": "Beginner", "Kafka": "Beginner", "Data Warehousing": "Intermediate"},
            "experience_level": "Mid"
        },
        "Senior Data Engineer": {
            "required_skills": {"Big Data": "Advanced", "Data Architecture": "Advanced", "ETL": "Advanced", "Cloud Platforms": "Intermediate", "Performance Optimization": "Advanced"},
            "preferred_skills": {"Stream Processing": "Intermediate", "Data Governance": "Intermediate", "Infrastructure": "Intermediate", "Team Leadership": "Intermediate"},
            "experience_level": "Senior"
        },
        "QA Engineer": {
            "required_skills": {"Testing": "Intermediate", "Test Automation": "Beginner", "Bug Tracking": "Intermediate", "Test Planning": "Intermediate"},
            "preferred_skills": {"Selenium": "Beginner", "API Testing": "Beginner", "Performance Testing": "Beginner", "CI/CD": "Beginner"},
            "experience_level": "Entry to Mid"
        },
        "Senior QA Engineer": {
            "required_skills": {"Test Automation": "Advanced", "Framework Development": "Intermediate", "Performance Testing": "Intermediate", "Leadership": "Intermediate"},
            "preferred_skills": {"Security Testing": "Intermediate", "Test Strategy": "Advanced", "Mentoring": "Intermediate", "Process Improvement": "Advanced"},
            "experience_level": "Senior"
        },
        "Security Engineer": {
            "required_skills": {"Cybersecurity": "Intermediate", "Network Security": "Intermediate", "Risk Assessment": "Intermediate", "Incident Response": "Intermediate"},
            "preferred_skills": {"Penetration Testing": "Beginner", "Compliance": "Intermediate", "Cloud Security": "Beginner", "Automation": "Beginner"},
            "experience_level": "Mid to Senior"
        },
        "Frontend Developer": {
            "required_skills": {"JavaScript": "Intermediate", "HTML": "Advanced", "CSS": "Advanced", "React": "Intermediate", "Web Development": "Intermediate"},
            "preferred_skills": {"TypeScript": "Beginner", "UI/UX Design": "Beginner", "Mobile Development": "Beginner", "Testing": "Beginner"},
            "experience_level": "Entry to Mid"
        },
        "Senior Frontend Developer": {
            "required_skills": {"JavaScript": "Advanced", "React": "Advanced", "TypeScript": "Intermediate", "Performance Optimization": "Intermediate", "Architecture": "Intermediate"},
            "preferred_skills": {"Next.js": "Intermediate", "State Management": "Intermediate", "Testing": "Intermediate", "Mentoring": "Intermediate"},
            "experience_level": "Senior"
        },
        "Backend Developer": {
            "required_skills": {"Python": "Intermediate", "API Development": "Intermediate", "Database": "Intermediate", "Server Management": "Intermediate"},
            "preferred_skills": {"Microservices": "Beginner", "Cloud Computing": "Beginner", "Security": "Beginner", "Performance Optimization": "Beginner"},
            "experience_level": "Entry to Mid"
        },
        "Senior Backend Developer": {
            "required_skills": {"System Design": "Intermediate", "Microservices": "Intermediate", "Database Optimization": "Intermediate", "API Architecture": "Intermediate"},
            "preferred_skills": {"Distributed Systems": "Intermediate", "Scalability": "Intermediate", "Security": "Intermediate", "Team Leadership": "Intermediate"},
            "experience_level": "Senior"
        }
    }


role_requirements = load_enhanced_role_requirements()

def enhanced_intent_detection_with_gemini(user_input, conversation_history, current_learning_path):
    """
    Enhanced intent detection using Gemini model to understand user's specific request
    and determine the appropriate action without regenerating the entire learning path
    """
    
    # Prepare context for Gemini
    context = {
        "current_learning_path": current_learning_path,
        "employee_profile": st.session_state.employee_profile,
        "learning_preferences": st.session_state.learning_preferences,
        "conversation_history": conversation_history[-3:] if conversation_history else []  # Last 3 messages
    }
    
    prompt = f"""
    You are an intelligent learning path assistant. Analyze the user's input to determine their intent and what action should be taken.
    
    CONTEXT:
    - Current Learning Path: {json.dumps(current_learning_path.get('learning_path', [])[:5]) if current_learning_path else ""}  # Show first 5 courses
    - Employee Skills: {json.dumps(st.session_state.employee_profile.get('skill_proficiency', {}))}
    - Recent Conversation: {json.dumps(context['conversation_history'])}
    
    USER INPUT: "{user_input}"
    
    Analyze the user's intent and respond with a JSON object containing:
    
    {{
        "intent_type": "add_skill|remove_skill|modify_learning_path|skill_gap_analysis|search_request|general_question|clarification_needed|out_of_context",
        "confidence": 0.0-1.0,
        "action_required": "regenerate_full_path|add_courses|remove_courses|search_web|provide_analysis|ask_clarification|respond_conversationally|ignore_request",
        "extracted_info": {{
            "skills_to_add": ["skill1", "skill2"],
            "skills_to_remove": ["skill3"],
            "time_constraint": null or number_of_weeks,
            "difficulty_preference": null or "beginner|intermediate|advanced",
            "search_query": null or "search terms",
            "specific_course_request": null or "course_name"
        }},
        "reasoning": "Brief explanation of why this intent was detected",
        "clarification_questions": ["question1", "question2"] or [],
        "response_suggestion": "Suggested response to user"
    }}
    
    INTENT DETECTION RULES:
    1. "add_skill" - User wants to learn NEW skills (e.g., "I want to learn AWS", "add Python to my path")
    2. "remove_skill" - User already knows something or wants to remove (e.g., "I already know Python", "remove JavaScript")
    3. "modify_learning_path" - User wants to change preferences (time, difficulty, etc.)
    4. "skill_gap_analysis" - User asks about gaps or what they should learn
    5. "search_request" - User wants to search for information
    6. "general_question" - Learning-related questions but no path changes needed
    7. "clarification_needed" - Input is ambiguous, need more info
    8. "out_of_context" - Completely unrelated to learning/career development
    
    ACTION RULES:
    - Only suggest "regenerate_full_path" if major changes are needed (career goal change, role change, etc.)
    - Use "add_courses" when user wants to learn new skills
    - Use "remove_courses" when user already knows skills
    - Use "ask_clarification" when input is ambiguous
    - Use "ignore_request" for completely off-topic requests
    
    Respond with valid JSON only.
    """
    
    try:
        generation_config = {
            "temperature": 0.2,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 1024,
        }
        
        response = gemini_model.generate_content(prompt, generation_config=generation_config)
        raw_text = response.text
        
        # Extract JSON from response
        match = re.search(r'```json\s*(\{[\s\S]*\})\s*```', raw_text)
        if match:
            json_str = match.group(1)
            result = json.loads(json_str)
        else:
            result = json.loads(raw_text)
        
        return result
        
    except Exception as e:
        st.error(f"Error in intent detection: {e}")
        return {
            "intent_type": "general_question",
            "confidence": 0.5,
            "action_required": "respond_conversationally",
            "extracted_info": {},
            "reasoning": "Error in processing, defaulting to general response",
            "clarification_questions": [],
            "response_suggestion": "I'm having trouble understanding your request. Could you please clarify what you'd like to learn or modify in your learning path?"
        }

# Extract structured information from user input
def extract_learning_requirements(user_input):
    user_input_lower = user_input.lower()
    
    # Extract time constraints
    time_patterns = [
        r"(\d+)\s*weeks?",
        r"(\d+)\s*months?",
        r"in\s*(\d+)\s*weeks?",
        r"within\s*(\d+)\s*weeks?"
    ]
    
    time_available = 0
    for pattern in time_patterns:
        match = re.search(pattern, user_input_lower)
        if match:
            time_value = int(match.group(1))
            if "month" in pattern:
                time_available = time_value * 4  # Convert months to weeks
            else:
                time_available = time_value
            break
    
    # Extract specific skills mentioned
    all_skills = set()
    for skills_dict in role_requirements.values():
        all_skills.update(skills_dict["required_skills"].keys())
        all_skills.update(skills_dict["preferred_skills"].keys())
    
    # Add skills from course catalog
    for _, course in course_catalog.iterrows():
        all_skills.update(course["skills"])
    
    mentioned_skills = [skill for skill in all_skills if skill.lower() in user_input_lower]
    
    # Extract urgency indicators
    urgency_keywords = {
        "critical": ["urgent", "immediately", "asap", "critical"],
        "high": ["soon", "quickly", "fast", "priority"],
        "medium": ["normal", "regular"],
        "low": ["eventually", "when possible", "no rush"]
    }
    
    urgency = "medium"
    for level, keywords in urgency_keywords.items():
        if any(keyword in user_input_lower for keyword in keywords):
            urgency = level
            break
    
    return {
        "time_available_weeks": time_available,
        "mentioned_skills": mentioned_skills,
        "urgency": urgency
    }

# Enhanced learning path generation with Udemy integration
def generate_enhanced_learning_path(employee_profile, learning_preferences, specific_requirements=None):
    # Prepare context
    current_role_reqs = role_requirements.get(employee_profile["current_role"], {})
    
    career_goal_reqs_list = []
    for goal in employee_profile["career_goals"]:
        career_goal_reqs_list.append(role_requirements.get(goal, {}))
    
    # Calculate skill gaps based on proficiency
    skill_gaps_with_proficiency = calculate_skill_gaps(
        employee_profile,
        current_role_reqs,
        career_goal_reqs_list
    )
    
    # Extract just the skill names from the gaps
    skill_gaps = [gap['Skill'] for gap in skill_gaps_with_proficiency]
    
    # Add specifically requested skills
    if learning_preferences.specific_skills_requested:
        skill_gaps.extend([skill for skill in learning_preferences.specific_skills_requested 
                          if skill not in skill_gaps]) # Only add if not already a gap
    
    if specific_requirements and specific_requirements.get("mentioned_skills"):
        skill_gaps.extend([skill for skill in specific_requirements["mentioned_skills"]
                          if skill not in skill_gaps])
    
    # Ensure skills_to_focus from specific_requirements are included
    if specific_requirements and specific_requirements.get("skills_to_focus"):
        skill_gaps.extend([skill for skill in specific_requirements["skills_to_focus"]
                           if skill not in skill_gaps])

    # Remove duplicates
    skill_gaps = list(set(skill_gaps))
    
    # Filter courses based on time constraints and preferences
    filtered_courses = course_catalog.copy()
    
    # Time constraint filtering
    time_constraint = learning_preferences.time_available_weeks
    if specific_requirements and specific_requirements.get("time_available_weeks"):
        time_constraint = specific_requirements["time_available_weeks"]
    
    if time_constraint > 0:
        # Allow some flexibility (±1 week)
        filtered_courses = filtered_courses[
            (filtered_courses["duration_weeks"] <= time_constraint + 1) &
            (filtered_courses["duration_weeks"] >= max(1, time_constraint - 2))
        ]
    
    # If shortening duration is requested, prioritize shorter courses
    if specific_requirements and specific_requirements.get("shorten_duration"):
        filtered_courses = filtered_courses.sort_values(by="duration_weeks", ascending=True)

    # Filter by relevant skills and proficiency
    relevant_courses = []
    employee_current_proficiency = employee_profile.get("skill_proficiency", {})

    for _, course in filtered_courses.iterrows():
        course_skills = course["skills"]
        course_difficulty = course["difficulty"]
        
        # Check if course addresses any identified skill gap at the appropriate proficiency level
        for gap_info in skill_gaps_with_proficiency:
            gap_skill = gap_info['Skill']
            target_proficiency = gap_info['Target Proficiency']
            current_proficiency = employee_current_proficiency.get(gap_skill, "Beginner")

            if gap_skill in course_skills:
                # Prioritize courses that move proficiency towards the target
                # This is a simplified logic; a more complex model could use a scoring system
                if get_proficiency_value(course_difficulty) >= get_proficiency_value(current_proficiency) and \
                   get_proficiency_value(course_difficulty) <= get_proficiency_value(target_proficiency):
                    if course["title"] not in employee_profile["completed_courses"]:
                        relevant_courses.append(course.to_dict())
                        break # Move to next course once a relevant gap is found

    # Generate Udemy courses for alternative suggestions
    udemy_courses = []
    skills_for_udemy = skill_gaps or learning_preferences.specific_skills_requested or []
    if skills_for_udemy:
        with st.spinner("🔍 Finding top Udemy courses..."):
            udemy_courses = udemy_agent.generate_udemy_courses(skills_for_udemy,employee_profile["current_role"])  # Limit to 3 skills
    
    # Create enhanced prompt
    prompt = f"""
    You are an expert learning path advisor. Create a personalized learning path for an employee.
    
    {'The user has requested a shorter duration learning path. Prioritize courses with shorter durations while still covering essential skills.' if specific_requirements and specific_requirements.get("shorten_duration") else ''}

    EMPLOYEE PROFILE:
    - Current Role: {employee_profile['current_role']}
    - Current Skills with Proficiency: {json.dumps(employee_profile.get('skill_proficiency', {}))}
    - Completed Courses: {', '.join(employee_profile['completed_courses'])}
    - Career Goals: {', '.join(employee_profile['career_goals'])}

    LEARNING CONSTRAINTS:
    - Time Available: {time_constraint} weeks (if specified)
    - Learning Style Preference: {learning_preferences.preferred_learning_style}
    - Difficulty Preference: {learning_preferences.difficulty_preference}
    - Urgency: {learning_preferences.learning_urgency}

    SKILL GAPS IDENTIFIED (with current and target proficiency):
    {json.dumps(skill_gaps_with_proficiency)}

    AVAILABLE COURSES (filtered by constraints and relevance):
    {json.dumps(relevant_courses[:15])}  # Limit to prevent token overflow

    SPECIFIC REQUIREMENTS:
    {json.dumps(specific_requirements) if specific_requirements else "None"}

    Create a learning path with 3-6 courses that:
    1. Addresses the most critical skill gaps first, prioritizing skills where current proficiency is significantly lower than target proficiency.
    2. Recommends courses that help the employee progress from their current proficiency level towards the target proficiency for each skill.
    3. Respects time constraints if specified.
    4. Follows logical learning progression.
    5. Matches the employee's preferred learning style when possible.

    For each recommended course:
    - Select from the AVAILABLE COURSES list
    - Provide title, type, duration, priority (Critical/High/Medium/Low)
    - Explain why it's recommended and how it fits the constraints
    - Indicate prerequisite relationships if any
    - Explicitly state how it helps bridge a specific skill gap and improve proficiency.
    - **Crucially, include the 'id' field for each internal course from the AVAILABLE COURSES list.**

    For alternative suggestions, focus on external learning resources and mention that Udemy courses will be provided separately.

    Return response in this JSON format:
    {{
      "learning_path": [
        {{
          "id": "COURSE_ID_FROM_CATALOG",
          "title": "Course Title",
          "type": "Course/Workshop/Bootcamp",
          "duration": "X weeks",
          "duration_weeks": X,
          "priority": "Critical/High/Medium/Low",
          "reason": "Detailed reason for recommendation, including how it addresses skill gap and proficiency.",
          "skills_gained": ["Skill1", "Skill2"],
          "fits_constraints": "How this course fits time/style constraints"
        }}
      ],
      "total_duration_weeks": X,
      "explanation": "Overall learning path strategy explanation, highlighting how proficiency gaps are addressed.",
      "skill_gaps_addressed": ["Skill1", "Skill2"],
      "progression_notes": "Notes about learning progression and dependencies, focusing on proficiency progression.",
      "alternative_suggestions": "Alternative approaches mentioning external resources like Udemy, Coursera, and free resources. Note that specific Udemy recommendations will be provided separately.",
      "udemy_courses": []
    }}

    Only respond with valid JSON.
    """
    
    try:
        generation_config = {
            "temperature": 0.1,  # Lower temperature for more consistent output
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
            }
        
        response = gemini_model.generate_content(
        prompt,
        generation_config=generation_config
        )
        raw_text = response.text
        
        # Extract JSON from markdown
        match = re.search(r'```json\s*(\{[\s\S]*\})\s*```', raw_text)
        if match:
            json_str = match.group(1)
            result = json.loads(json_str)
        else:
            # Try to parse the entire response as JSON
            result = json.loads(raw_text)
        
        # Add Udemy courses to the result
        result["udemy_courses"] = [
            {
                "id": course.id, # Include ID for Udemy courses
                "title": course.title,
                "url": course.url,
                "description": course.description,
                "rating": course.rating,
                "price": course.price,
                "duration": course.duration,
                "level": course.level
            }
            for course in udemy_courses
        ]
        
        return result
        
    except Exception as e:
        st.error(f"Error generating learning path: {e}")
        return {
            "learning_path": [],
            "explanation": "Error generating learning path. Please try again.",
            "skill_gaps_addressed": [],
            "total_duration_weeks": 0,
            "progression_notes": "",
            "alternative_suggestions": "",
            "udemy_courses": []
        }

#update
def add_courses_to_learning_path(current_path, skills_to_add, employee_profile, learning_preferences):
    """
    Add new courses for specific skills without regenerating the entire path
    """
    
    # Filter courses for the new skills
    new_courses = []
    filtered_courses = course_catalog.copy()
    
    # Apply existing time constraints
    time_constraint = learning_preferences.time_available_weeks
    if time_constraint > 0:
        filtered_courses = filtered_courses[
            (filtered_courses["duration_weeks"] <= time_constraint + 1) &
            (filtered_courses["duration_weeks"] >= max(1, time_constraint - 2))
        ]
    
    # Find courses for new skills
    for _, course in filtered_courses.iterrows():
        if any(skill.lower() in [s.lower() for s in course["skills"]] for skill in skills_to_add):
            if course["title"] not in employee_profile["completed_courses"]:
                # Check if course is not already in learning path
                existing_titles = [c.get("title", "") for c in current_path.get("learning_path", [])] if current_path else []
                if course["title"] not in existing_titles:
                    new_courses.append({
                        "id": course["id"], # Include ID
                        "title": course["title"],
                        "type": course["type"],
                        "duration": f"{course['duration_weeks']} weeks",
                        "duration_weeks": course["duration_weeks"],
                        "priority": "High",  # New requested skills get high priority
                        "reason": f"Added based on your request to learn {', '.join(skills_to_add)}",
                        "skills_gained": course["skills"],
                        "fits_constraints": "Matches your learning preferences and time constraints"
                    })
    
    # Generate Udemy courses for new skills
    new_udemy_courses = []
    if skills_to_add:
        with st.spinner("🔍 Finding additional Udemy courses..."):
            new_udemy_courses = udemy_agent.generate_udemy_courses(skills_to_add, employee_profile["current_role"])
    
    # Update the learning path
    if current_path:
        updated_path = current_path.copy()
    else:
        updated_path = {}
        updated_path["learning_path"] = []
    updated_path["learning_path"].extend(new_courses)
    #updated_path["learning_path"] = []
    # Add new Udemy courses (avoid duplicates)
    existing_udemy_titles = [c.get("title", "") for c in updated_path.get("udemy_courses", [])] if updated_path else []
    for course in new_udemy_courses:
        if course.title not in existing_udemy_titles:
            updated_path["udemy_courses"].append({
                "id": course.id, # Include ID
                "title": course.title,
                "url": course.url,
                "description": course.description,
                "rating": course.rating,
                "price": course.price,
                "duration": course.duration,
                "level": course.level
            })
    
    # Update metadata
    updated_path["total_duration_weeks"] = sum(c.get("duration_weeks", 0) for c in updated_path["learning_path"])
    updated_path["skill_gaps_addressed"].extend(skills_to_add)
    updated_path["explanation"] += f"\n\n🆕 Added courses for: {', '.join(skills_to_add)}"
    
    return updated_path, new_courses

def remove_courses_from_learning_path(current_path, skills_to_remove):
    """
    Remove courses related to specific skills that user already knows
    """
    if current_path:
        updated_path = current_path.copy()
    removed_courses = []
    
    # Remove internal courses
    remaining_courses = []
    for course in updated_path.get("learning_path", []):
        course_skills = course.get("skills_gained", [])
        # Check if any of the course skills match skills to remove
        if any(skill.lower() in [s.lower() for s in course_skills] for skill in skills_to_remove):
            removed_courses.append(course["title"])
        else:
            remaining_courses.append(course)
    
    updated_path["learning_path"] = remaining_courses
    
    # Remove Udemy courses
    remaining_udemy = []
    for course in updated_path.get("udemy_courses", []):
        # Check if course title or description contains the skills to remove
        course_text = f"{course.get('title', '')} {course.get('description', '')}".lower()
        if not any(skill.lower() in course_text for skill in skills_to_remove):
            remaining_udemy.append(course)
    
    updated_path["udemy_courses"] = remaining_udemy
    
    # Update metadata
    updated_path["total_duration_weeks"] = sum(c.get("duration_weeks", 0) for c in updated_path["learning_path"])
    updated_path["skill_gaps_addressed"] = [s for s in updated_path.get("skill_gaps_addressed", []) 
                                          if s.lower() not in [skill.lower() for skill in skills_to_remove]]
    updated_path["explanation"] += f"\n\n🗑️ Removed courses for skills you already know: {', '.join(skills_to_remove)}"
    
    return updated_path, removed_courses

def process_enhanced_user_input(user_input):
    """
    Enhanced user input processing with intelligent intent detection and incremental learning path updates
    """
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🤔 Understanding your request...")
    
    # Get current learning path
    current_learning_path = st.session_state.get('learning_path', {})
    conversation_history = st.session_state.get('messages', [])
    
    # Enhanced intent detection using Gemini
    intent_result = enhanced_intent_detection_with_gemini(user_input, conversation_history, current_learning_path)
    
    # Process based on detected intent
    if intent_result["action_required"] == "ignore_request":
        response = "I'm focused on helping you with learning and career development. " + intent_result["response_suggestion"]
    
    elif intent_result["action_required"] == "ask_clarification":
        response = f"I need a bit more information to help you better.\n\n"
        for question in intent_result["clarification_questions"]:
            response += f"• {question}\n"
        response += f"\n{intent_result['response_suggestion']}"
    
    elif intent_result["action_required"] == "add_courses":
        message_placeholder.markdown("➕ Adding new courses to your learning path...")
        
        skills_to_add = intent_result["extracted_info"].get("skills_to_add", [])
        if skills_to_add:
            updated_path, new_courses = add_courses_to_learning_path(
                current_learning_path, 
                skills_to_add, 
                st.session_state.employee_profile, 
                st.session_state.learning_preferences
            )
            st.session_state.learning_path = updated_path
            
            # Sync with employee database
            employee_id = get_current_employee_id()
            if employee_id:
                sync_employee_learning_path(employee_id, updated_path)
                # Initialize progress for newly added courses
                for course in new_courses:
                    course_id = course.get('id')
                    if course_id and employee_id not in st.session_state.learning_path_progress:
                        st.session_state.learning_path_progress[employee_id] = {}
                    if course_id:
                        st.session_state.learning_path_progress[employee_id][course_id] = {
                            "status": "Not Started", 
                            "start_date": None, 
                            "completion_date": None
                        }
            
            response = f"✅ **Added {len(new_courses)} new courses to your learning path for: {', '.join(skills_to_add)}**\n\n"
            response += "**New Courses Added:**\n"
            for course in new_courses:
                response += f"• **{course['title']}** ({course['duration']}) - {course['reason']}\n"
            
            response += f"\n📊 **Updated Path Summary:**\n"
            response += f"• Total Courses: {len(updated_path['learning_path'])}\n"
            response += f"• Total Duration: {updated_path['total_duration_weeks']} weeks\n"
            response += f"• Udemy Courses: {len(updated_path.get('udemy_courses', []))}\n\n"
            response += "Check the learning path panel to see all your courses!"
        else:
            response = "I couldn't identify specific skills to add. Could you please specify which skills you'd like to learn?"
    
    elif intent_result["action_required"] == "remove_courses":
        message_placeholder.markdown("🗑️ Removing courses from your learning path...")
        
        skills_to_remove = intent_result["extracted_info"].get("skills_to_remove", [])
        if skills_to_remove:
            updated_path, removed_courses = remove_courses_from_learning_path(current_learning_path, skills_to_remove)
            st.session_state.learning_path = updated_path
            
            # Sync with employee database
            employee_id = get_current_employee_id()
            if employee_id:
                sync_employee_learning_path(employee_id, updated_path)
                # Remove progress for removed courses
                if employee_id in st.session_state.learning_path_progress:
                    for course_title in removed_courses:
                        # Find course ID by title (less robust, but needed if ID not passed)
                        course_id_to_remove = None
                        for course_type_list in [updated_path.get("learning_path", []), updated_path.get("udemy_courses", [])]:
                            for c in course_type_list:
                                if c.get('title') == course_title:
                                    course_id_to_remove = c.get('id')
                                    break
                            if course_id_to_remove: break

                        if course_id_to_remove and course_id_to_remove in st.session_state.learning_path_progress[employee_id]:
                            del st.session_state.learning_path_progress[employee_id][course_id_to_remove]

            
            response = f"✅ **Removed courses for skills you already know: {', '.join(skills_to_remove)}**\n\n"
            if removed_courses:
                response += "**Courses Removed:**\n"
                for course_title in removed_courses:
                    response += f"• {course_title}\n"
            
            response += f"\n📊 **Updated Path Summary:**\n"
            response += f"• Total Courses: {len(updated_path['learning_path'])}\n"
            response += f"• Total Duration: {updated_path['total_duration_weeks']} weeks\n"
            response += f"• Udemy Courses: {len(updated_path.get('udemy_courses', []))}\n\n"
            response += "Your learning path has been optimized based on your existing knowledge!"
        else:
            response = "I couldn't identify which skills to remove. Could you please specify which skills you already know?"
    
    elif intent_result["action_required"] == "regenerate_full_path":
        message_placeholder.markdown("🔄 Regenerating your complete learning path...")
        
        # Extract any new requirements
        specific_requirements = intent_result["extracted_info"]
        
        # Update learning preferences if needed
        if specific_requirements.get("time_constraint"):
            st.session_state.learning_preferences.time_available_weeks = specific_requirements["time_constraint"]
        
        # Regenerate full path
        result = generate_enhanced_learning_path_with_sync(
            st.session_state.employee_profile,
            st.session_state.learning_preferences,
            specific_requirements
        )
        st.session_state.learning_path = result
        
        # Reset progress for the new path
        employee_id = get_current_employee_id()
        if employee_id:
            st.session_state.learning_path_progress[employee_id] = {}
            for course in result.get('learning_path', []):
                course_id = course.get('id')
                if course_id:
                    st.session_state.learning_path_progress[employee_id][course_id] = {
                        "status": "Not Started", 
                        "start_date": None, 
                        "completion_date": None
                    }
            for course in result.get('udemy_courses', []):
                course_id = course.get('id')
                if course_id:
                    st.session_state.learning_path_progress[employee_id][course_id] = {
                        "status": "Not Started", 
                        "start_date": None, 
                        "completion_date": None
                    }

        response = f"🔄 **Complete Learning Path Regenerated!**\n\n"
        response += f"**Reason:** {intent_result['reasoning']}\n\n"
        response += f"**New Path Summary:**\n"
        response += f"• Total Courses: {len(result.get('learning_path', []))}\n"
        response += f"• Total Duration: {result.get('total_duration_weeks', 0)} weeks\n"
        response += f"• Udemy Courses: {len(result.get('udemy_courses', []))}\n\n"
        response += f"**Strategy:** {result.get('explanation', '')}"
    
    elif intent_result["action_required"] == "search_web":
        message_placeholder.markdown("🔍 Searching the web for information...")
        
        search_query = intent_result["extracted_info"].get("search_query", user_input)
        search_results = search_agent.search_web(search_query, max_results=5)
        
        if search_results:
            response = f"🔍 **Search Results for: {search_query}**\n\n"
            for i, result in enumerate(search_results, 1):
                response += f"**{i}. {result['title']}**\n"
                response += f"🔗 {result['url']}\n"
                response += f"📝 {result['snippet'][:200]}...\n\n"
            response += "Would you like me to add any of these topics to your learning path?"
        else:
            response = f"I couldn't find specific search results for '{search_query}'. Would you like me to suggest some learning resources instead?"
    
    elif intent_result["action_required"] == "provide_analysis":
        message_placeholder.markdown("📊 Analyzing your skills and learning path...")
        
        # Provide skill gap analysis or learning path analysis
        response = intent_result["response_suggestion"]
        
        # Add current learning path status if available
        if current_learning_path:
            response += f"\n\n📈 **Current Learning Path Status:**\n"
            response += f"• Active Courses: {len(current_learning_path.get('learning_path', []))}\n"
            response += f"• Skills Being Developed: {', '.join(current_learning_path.get('skill_gaps_addressed', []))}\n"
            response += f"• Estimated Completion: {current_learning_path.get('total_duration_weeks', 0)} weeks"
    
    else:  # respond_conversationally
        response = intent_result["response_suggestion"]
    
    # Add confidence and reasoning for debugging (optional)
    if intent_result["confidence"] < 0.7:
        response += f"\n\n💭 *I'm {int(intent_result['confidence']*100)}% confident in my understanding. If this isn't what you meant, please let me know!*"
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    message_placeholder.markdown(response)



# Enhanced employee profile update function
def update_employee_profile():
    with st.sidebar.expander("👤 Edit Employee Profile", expanded=False):
        # Basic Information
        st.markdown("#### Basic Information")
        name = st.text_input("Name", value=st.session_state.employee_profile["name"])
        
        current_role = st.selectbox(
            "Current Role", 
            options=list(role_requirements.keys()), 
            index=list(role_requirements.keys()).index(st.session_state.employee_profile["current_role"]) 
            if st.session_state.employee_profile["current_role"] in role_requirements else 0
        )
        
        # Skills Section
        st.markdown("#### Skills & Proficiency")
        
        # Get all available skills from role requirements
        all_skills = set()
        for role_data in role_requirements.values():
            all_skills.update(role_data["required_skills"].keys())
            all_skills.update(role_data["preferred_skills"].keys())
        
        # Add skills from course catalog
        for _, course in course_catalog.iterrows():
            all_skills.update(course["skills"])
        
        skills = st.multiselect(
            "Current Skills", 
            options=sorted(list(all_skills)), 
            default=list(st.session_state.employee_profile.get("skill_proficiency", {}).keys()), # Use keys from skill_proficiency
            help="Select all skills you currently possess"
        )
        
        # Skill Proficiency Levels
        st.markdown("#### Skill Proficiency Levels")
        proficiency_levels = ["Beginner", "Intermediate", "Advanced", "Expert"]
        skill_proficiency = {}
        if skills:
            for skill in skills:
                current_proficiency = st.session_state.employee_profile.get("skill_proficiency", {}).get(skill, "Beginner")
                
                # Ensure the current_proficiency is in the list before finding index
                if current_proficiency not in proficiency_levels:
                    current_proficiency = "Beginner" # Fallback if proficiency is invalid
                
                proficiency = st.selectbox(
                    f"Proficiency in {skill}",
                    proficiency_levels,
                    index=proficiency_levels.index(current_proficiency),
                    key=f"prof_{skill}"
                )
                skill_proficiency[skill] = proficiency
        
        # Career Goals
        st.markdown("#### Career Goals")
        career_goals = st.multiselect(
            "Career Aspirations", 
            options=list(role_requirements.keys()), 
            default=st.session_state.employee_profile["career_goals"],
            help="Select roles you aspire to achieve"
        )
        
        # Completed Courses
        st.markdown("#### Learning History")
        all_courses = course_catalog["title"].tolist()
        completed_courses = st.multiselect(
            "Completed Courses", 
            options=all_courses,
            default=st.session_state.employee_profile["completed_courses"],
            help="Select courses you have already completed"
        )
        
        # Experience Level
        experience_level = st.selectbox(
            "Overall Experience Level",
            ["Entry Level", "Junior", "Mid-level", "Senior", "Expert"],
            index=["Entry Level", "Junior", "Mid-level", "Senior", "Expert"].index(
                st.session_state.employee_profile.get("experience_level", "Mid-level")
            )
        )
        
        # Update button
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Update Profile", type="primary"):
                st.session_state.employee_profile = {
                    "employee_id": st.session_state.employee_profile["employee_id"],
                    "name": name,
                    "current_role": current_role,
                    "skills": list(skill_proficiency.keys()), # Update skills list based on proficiency keys
                    "skill_proficiency": skill_proficiency,
                    "completed_courses": completed_courses,
                    "career_goals": career_goals,
                    "experience_level": experience_level
                }
                
                # Reset learning path when profile is updated
                st.session_state.learning_path = None
                
                # Add system message about profile update
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"✅ Profile updated successfully! Your new profile shows {len(skills)} skills and {len(career_goals)} career goals. Would you like me to create a new learning path based on your updated profile?"
                })
                st.success("Profile updated successfully!")
                st.rerun()
        
        with col2:
            if st.button("🔄 Reset to Default"):
                st.session_state.employee_profile = {
                    "employee_id": "EMP123456",
                    "name": "Aditya Gupta",
                    "current_role": "Data Analyst",
                    "skills": ["SQL", "Excel", "Data Visualization", "Python"],
                    "completed_courses": ["Data Analysis Fundamentals", "Excel Advanced", "SQL Intermediate"],
                    "career_goals": ["Senior Data Analyst"], # Changed to list for consistency
                    "skill_proficiency": {
                        "SQL": "Intermediate",
                        "Excel": "Advanced", 
                        "Data Visualization": "Intermediate",
                        "Python": "Beginner"
                    },
                    "experience_level": "Mid-level",
                }
                st.info("Profile reset to default values!")
                st.rerun()

# --- Save/Load Functions for Persistence ---
def save_all_learning_paths():
    """Saves the entire employee database and learning path progress to a JSON file."""
    data_to_save = {
        "employee_database": st.session_state.employee_database,
        "learning_path_progress": st.session_state.learning_path_progress
    }
    try:
        with open(st.session_state.saved_learning_paths_file, 'w') as f:
            json.dump(data_to_save, f, indent=4)
        st.success("All learning paths and progress saved successfully!")
    except Exception as e:
        st.error(f"Error saving data: {e}")

def load_all_learning_paths():
    """Loads the entire employee database and learning path progress from a JSON file."""
    try:
        if os.path.exists(st.session_state.saved_learning_paths_file):
            with open(st.session_state.saved_learning_paths_file, 'r') as f:
                loaded_data = json.load(f)
            
            st.session_state.employee_database = loaded_data.get("employee_database", load_employee_database())
            st.session_state.learning_path_progress = loaded_data.get("learning_path_progress", {})
            
            st.success("Learning paths and progress loaded successfully!")
            st.rerun()
        else:
            st.warning("No saved data found. Starting with default employee data.")
            st.session_state.employee_database = load_employee_database()
            st.session_state.learning_path_progress = {} # Ensure it's initialized if no file
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.session_state.employee_database = load_employee_database() # Fallback to default
        st.session_state.learning_path_progress = {}


# Enhanced sidebar with learning preferences and search features
def enhanced_sidebar():
    with st.sidebar:
        st.image("https://via.placeholder.com/150x150/4CAF50/white?text=AI", width=150)
        st.title("🧠 Smart Learning Advisor")
        st.markdown("*Powered by AI Search & Udemy Integration*")
        
        st.markdown(f"### {st.session_state.employee_profile['name']}")
        st.markdown(f"**Role:** {st.session_state.employee_profile['current_role']}")
        st.markdown(f"**Experience:** {st.session_state.employee_profile.get('experience_level', 'Mid-level')}")
        
        # Employee Profile Editing
        update_employee_profile()
        
        # Current skills with proficiency
        with st.expander("📊 Current Skills & Proficiency", expanded=True):
            if st.session_state.employee_profile["skill_proficiency"]:
                for skill, proficiency in st.session_state.employee_profile["skill_proficiency"].items():
                    proficiency_emoji = {"Beginner": "🟢", "Intermediate": "🟡", "Advanced": "🔴", "Expert": "🟣"}.get(proficiency, "⚪")
                    st.markdown(f"{proficiency_emoji} **{skill}** - {proficiency}")
            else:
                st.info("No skills added yet. Edit your profile to add skills.")
        
        # Career goals
        with st.expander("🎯 Career Goals"):
            if st.session_state.employee_profile["career_goals"]:
                for goal in st.session_state.employee_profile["career_goals"]:
                    st.markdown(f"• {goal}")
            else:
                st.info("No career goals set. Edit your profile to add goals.")
        
        # Completed courses
        with st.expander("📚 Completed Courses"):
            if st.session_state.employee_profile["completed_courses"]:
                for course in st.session_state.employee_profile["completed_courses"]:
                    st.markdown(f"✅ {course}")
            else:
                st.info("No completed courses recorded.")
        
        # Learning preferences section
        with st.expander("⚙️ Learning Preferences", expanded=False):
            st.session_state.learning_preferences.time_available_weeks = st.number_input(
                "Time Available (weeks)", 
                min_value=0, 
                max_value=52, 
                value=st.session_state.learning_preferences.time_available_weeks,
                help="How many weeks can you dedicate to learning?"
            )
            
            st.session_state.learning_preferences.preferred_learning_style = st.selectbox(
                "Learning Style",
                ["Mixed", "Visual", "Hands-on", "Interactive", "Intensive"],
                index=["Mixed", "Visual", "Hands-on", "Interactive", "Intensive"].index(
                    st.session_state.learning_preferences.preferred_learning_style
                )
            )
            
            st.session_state.learning_preferences.difficulty_preference = st.selectbox(
                "Difficulty Preference",
                ["Progressive", "Beginner", "Intermediate", "Advanced"],
                index=["Progressive", "Beginner", "Intermediate", "Advanced"].index(
                    st.session_state.learning_preferences.difficulty_preference
                )
            )
            
            st.session_state.learning_preferences.learning_urgency = st.selectbox(
                "Learning Urgency",
                ["Low", "Medium", "High", "Critical"],
                index=["Low", "Medium", "High", "Critical"].index(
                    st.session_state.learning_preferences.learning_urgency
                )
            )
            
            # Skill request interface
            all_skills = set()
            for role_data in role_requirements.values():
                all_skills.update(role_data["required_skills"].keys())
                all_skills.update(role_data["preferred_skills"].keys())
            
            additional_skills = st.multiselect(
                "Additional Skills to Learn",
                options=sorted(list(all_skills)),
                default=st.session_state.learning_preferences.specific_skills_requested or [],
                help="Select specific skills you want to focus on"
            )
            st.session_state.learning_preferences.specific_skills_requested = additional_skills
        
        # Enhanced Quick Actions
        st.markdown("### 🚀 Quick Actions")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎯 Generate\nLearning Path", type="primary"):
                process_enhanced_user_input("Create a personalized learning path for me based on my preferences")
        
        with col2:
            if st.button("📈 Analyze\nSkill Gaps"):
                process_enhanced_user_input("What are my skill gaps for my current role?")
        
        col3, col4 = st.columns(2)
        with col3:
            if st.button("⏱️ Quick 2-Week\nPlan"):
                process_enhanced_user_input("I have 2 weeks to learn new skills, what do you recommend?")
        
        with col4:
            if st.button("🔍 Search\nResources"):
                if st.session_state.learning_preferences.specific_skills_requested:
                    skills_text = ', '.join(st.session_state.learning_preferences.specific_skills_requested[:2])
                    process_enhanced_user_input(f"Search for learning resources about {skills_text}")
                else:
                    process_enhanced_user_input("Search for learning resources about data science")
        
        # Search Interface
        with st.expander("🔍 AI Search Assistant", expanded=False):
            st.markdown("**Search the web for learning resources, trends, or information:**")
            search_query = st.text_input(
                "Enter search query:",
                placeholder="e.g., 'latest machine learning trends 2024'",
                key="search_input"
            )
            
            col_search1, col_search2 = st.columns(2)
            with col_search1:
                if st.button("🔍 Search Web", key="web_search"):
                    if search_query:
                        process_enhanced_user_input(f"Search for {search_query}")
                    else:
                        st.warning("Please enter a search query")
            
            with col_search2:
                if st.button("📚 Find Courses", key="course_search"):
                    if search_query:
                        process_enhanced_user_input(f"Find courses about {search_query}")
                    else:
                        st.warning("Please enter a topic")
        
        

        # Reset and Help
        col_reset, col_help = st.columns(2)
        with col_reset:
            if st.button("🔄 Reset Chat"):
                st.session_state.messages = [
                    {"role": "assistant", "content": "Hello! I'm your enhanced learning advisor with AI-powered search capabilities. I can help you create personalized learning paths and find the best Udemy courses. How can I assist you today?"}
                ]
                st.session_state.learning_path = None
                st.rerun()
        
        with col_help:
            if st.button("❓ Help"):
                help_message = """
                **Available Commands:**
                • "Create a learning path for [skill]"
                • "I have [X] weeks to learn [skill]"
                • "Search for information about [topic]"
                • "What are my skill gaps?"
                • "Find Udemy courses for [skill]"
                • "Show me beginner courses only"
                """
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": help_message
                })
                st.rerun()

# Enhanced main interface with better layout
def enhanced_main():
    enhanced_sidebar()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 💬 Smart Learning Assistant")
        st.markdown("*Ask about learning paths, search for resources, or get Udemy course recommendations*")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Enhanced chat input with suggestions
        user_input = st.chat_input("Ask about learning paths, search topics, or request Udemy courses...")
        if user_input:
            process_enhanced_user_input(user_input)
    
    with col2:
        # Enhanced learning path display
        enhanced_learning_path_management()

# Footer with credits
def add_footer():
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>🧠 <strong>Smart Learning Path Advisor</strong></p>
        <p>Powered by Google Gemini AI • Enhanced with DuckDuckGo Search • Udemy Course Integration</p>
        <p><small>Built with ❤️ using Streamlit • AI-Powered Learning Recommendations</small></p>
    </div>
    """, unsafe_allow_html=True)

# Run the enhanced app
if __name__ == "__main__":
    main_with_navigation()
    add_footer()

