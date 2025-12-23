"""
Parallel build script for SingBox-UI and updater executables.
Builds both exe files simultaneously to speed up the build process.
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from multiprocessing import Process, Queue
from typing import Optional


def build_exe(spec_file: str, output_queue: Queue):
    """Build a single exe file from spec file."""
    spec_path = Path(spec_file)
    if not spec_path.exists():
        output_queue.put((spec_file, False, f"Spec file not found: {spec_file}"))
        return
    
    print(f"[BUILD] Starting build: {spec_file}")
    start_time = time.time()
    
    try:
        # Run pyinstaller
        result = subprocess.run(
            [sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm', str(spec_path)],
            capture_output=True,
            text=True,
            check=True
        )
        
        elapsed = time.time() - start_time
        output_queue.put((spec_file, True, f"Build completed in {elapsed:.1f}s"))
        print(f"[BUILD] [OK] {spec_file} completed in {elapsed:.1f}s")
        
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        error_msg = f"Build failed after {elapsed:.1f}s: {e.stderr or e.stdout or str(e)}"
        output_queue.put((spec_file, False, error_msg))
        print(f"[BUILD] [FAIL] {spec_file} failed: {error_msg}")
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"Unexpected error after {elapsed:.1f}s: {str(e)}"
        output_queue.put((spec_file, False, error_msg))
        print(f"[BUILD] [FAIL] {spec_file} error: {error_msg}")


def clean_build_dirs(project_root: Path, clean_build: bool = True, clean_dist: bool = False):
    """Clean build and dist directories to speed up build."""
    if clean_build:
        build_dir = project_root / 'build'
        if build_dir.exists():
            print(f"[CLEAN] Removing build directory: {build_dir}")
            try:
                shutil.rmtree(build_dir)
                print(f"[CLEAN] [OK] Build directory cleaned")
            except Exception as e:
                print(f"[CLEAN] WARNING: Could not clean build directory: {e}")
    
    if clean_dist:
        dist_dir = project_root / 'dist'
        if dist_dir.exists():
            print(f"[CLEAN] Removing dist directory: {dist_dir}")
            try:
                shutil.rmtree(dist_dir)
                print(f"[CLEAN] [OK] Dist directory cleaned")
            except Exception as e:
                print(f"[CLEAN] WARNING: Could not clean dist directory: {e}")


def main():
    """Main function to build both exe files in parallel."""
    parser = argparse.ArgumentParser(
        description='Parallel build script for SingBox-UI and updater executables'
    )
    parser.add_argument(
        '--clean-build',
        action='store_true',
        help='Clean build directory before building (recommended for faster builds)'
    )
    parser.add_argument(
        '--clean-dist',
        action='store_true',
        help='Clean dist directory before building (removes old executables)'
    )
    parser.add_argument(
        '--clean-all',
        action='store_true',
        help='Clean both build and dist directories before building'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("SingBox-UI Parallel Build Script")
    print("=" * 60)
    print()
    
    # Check if we're in the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Clean directories if requested
    if args.clean_all:
        clean_build_dirs(project_root, clean_build=True, clean_dist=True)
    else:
        clean_build_dirs(project_root, clean_build=args.clean_build, clean_dist=args.clean_dist)
    
    if args.clean_build or args.clean_dist or args.clean_all:
        print()
    
    # Spec files to build
    spec_files = [
        'SingBox-UI.spec',
        'updater.spec'
    ]
    
    # Check if spec files exist
    missing_specs = [spec for spec in spec_files if not Path(spec).exists()]
    if missing_specs:
        print(f"ERROR: Spec files not found: {', '.join(missing_specs)}")
        sys.exit(1)
    
    # Check if PyInstaller is available
    try:
        subprocess.run(
            [sys.executable, '-m', 'PyInstaller', '--version'],
            capture_output=True,
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: PyInstaller not found. Install it with: pip install pyinstaller")
        sys.exit(1)
    
    print(f"Building {len(spec_files)} executables in parallel...")
    print()
    
    # Create queue for results
    result_queue = Queue()
    
    # Start build processes
    processes = []
    start_time = time.time()
    
    for spec_file in spec_files:
        p = Process(target=build_exe, args=(spec_file, result_queue))
        p.start()
        processes.append(p)
    
    # Wait for all processes to complete
    for p in processes:
        p.join()
    
    # Collect results
    results = []
    while not result_queue.empty():
        results.append(result_queue.get())
    
    total_time = time.time() - start_time
    
    # Print summary
    print()
    print("=" * 60)
    print("Build Summary")
    print("=" * 60)
    
    success_count = 0
    for spec_file, success, message in results:
        status = "[OK] SUCCESS" if success else "[FAIL] FAILED"
        print(f"{status}: {spec_file}")
        print(f"  {message}")
        if success:
            success_count += 1
    
    print()
    print(f"Total time: {total_time:.1f}s")
    print(f"Success: {success_count}/{len(spec_files)}")
    print("=" * 60)
    
    # Run post-build script if all builds succeeded
    if success_count == len(spec_files):
        post_build_script = project_root / 'main' / 'post_build.py'
        if post_build_script.exists():
            print()
            print("Running post-build script...")
            try:
                subprocess.run(
                    [sys.executable, str(post_build_script)],
                    check=True
                )
                print("[OK] Post-build script completed")
            except subprocess.CalledProcessError as e:
                print(f"[FAIL] Post-build script failed: {e}")
                sys.exit(1)
        else:
            print("WARNING: post_build.py not found, skipping post-build step")
    
    # Exit with error code if any build failed
    if success_count < len(spec_files):
        sys.exit(1)


if __name__ == '__main__':
    main()

