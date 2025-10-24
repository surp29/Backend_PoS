#!/bin/bash
# Script để push Backend code lên GitHub

echo "🚀 Pushing Backend code to GitHub..."

# Add all files
git add .

# Commit changes
git commit -m "Update PoS Backend - Ready for Render.com deployment"

# Add remote origin
git remote add origin https://github.com/surp29/Backend_PoS.git

# Push to main branch
git branch -M main
git push -u origin main

echo "✅ Backend code pushed successfully!"
