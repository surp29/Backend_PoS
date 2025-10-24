#!/usr/bin/env python3
"""
Database setup script for Render.com deployment
This script will create the database tables and initial data
"""

import os
import sys
from sqlalchemy import create_engine, text
from app.database import Base, engine
from app.models import *
from app.config import Config

def setup_database():
    """Setup database tables and initial data"""
    try:
        print("🗄️ Setting up database...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        # Test database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection test successful")
        
        print("🎉 Database setup completed!")
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting PoS Database Setup")
    print(f"🔗 Database URL: {Config.SQLALCHEMY_DATABASE_URI}")
    print()
    
    success = setup_database()
    
    if success:
        print("✅ Database setup completed successfully!")
        sys.exit(0)
    else:
        print("❌ Database setup failed!")
        sys.exit(1)
