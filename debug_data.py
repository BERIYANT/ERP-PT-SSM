#!/usr/bin/env python
from app import create_app
from models import db, Project, ProjectRAB, Material, PettyCash

app = create_app('development')
with app.app_context():
    # Get any project
    project = Project.query.first()
    if project:
        print('=== Project Found ===')
        print(f'Project ID: {project.id}')
        print(f'Project Name: {project.project_name}')
        print(f'Project Amount: {project.amount}')
        print()
        
        # Check RAB data
        rab_items = ProjectRAB.query.filter_by(project_id=project.id).all()
        print(f'RAB Items: {len(rab_items)}')
        for rab in rab_items:
            print(f'  - {rab.kategori}: {rab.total}')
        print()
        
        # Check Material data
        materials = Material.query.filter_by(project_id=project.id).all()
        print(f'Materials for this project: {len(materials)}')
        for mat in materials:
            print(f'  - {mat.name}: Rp {mat.price}')
        print()
        
        # Check Petty Cash data
        petty = PettyCash.query.filter_by(project_id=project.id).all()
        print(f'Petty Cash Items for this project: {len(petty)}')
        for p in petty:
            print(f'  - {p.kategori}: Rp {p.jumlah}')
        print()
        
        # Also check ALL materials (without project filter)
        all_materials = Material.query.all()
        print(f'Total Materials in DB (all): {len(all_materials)}')
        for mat in all_materials:
            print(f'  - {mat.name}: project_id={mat.project_id}, price=Rp {mat.price}')
        
        # Check ALL petty cash
        all_petty = PettyCash.query.all()
        print(f'Total Petty Cash in DB (all): {len(all_petty)}')
        for p in all_petty:
            print(f'  - {p.kategori}: project_id={p.project_id}, jumlah=Rp {p.jumlah}')
    else:
        print('No projects found')
