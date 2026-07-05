"""
LightSpeed V0.9.5 - IT Portal Structure Fix
Fixes critical P0 blocker: methods defined outside ITPortal class
Date: January 2, 2026
"""

from pathlib import Path
import re

def fix_it_portal_structure():
    """Fix IT Portal class structure by moving misplaced methods"""

    # Get IT Portal path
    script_dir = Path(__file__).parent
    it_portal_path = script_dir.parent.parent.parent / "core" / "ui" / "it_portal.py"

    if not it_portal_path.exists():
        print(f"[ERROR] IT Portal not found at: {it_portal_path}")
        return False

    print("=" * 70)
    print("LIGHTSPEED V1.0.0 - IT PORTAL STRUCTURE FIX")
    print("=" * 70)
    print(f"\nFile: {it_portal_path}")
    print(f"Size: {it_portal_path.stat().st_size / 1024:.2f} KB\n")

    # Backup first
    backup_path = it_portal_path.parent / f"{it_portal_path.stem}_backup_structure.py"
    print(f"[1/5] Creating backup: {backup_path.name}")

    try:
        import shutil
        shutil.copy2(it_portal_path, backup_path)
        print(f"[OK] Backup created\n")
    except Exception as e:
        print(f"[ERROR] Backup failed: {e}")
        return False

    # Read the file
    print("[2/5] Reading file...")
    with open(it_portal_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    print(f"[OK] Read {len(lines)} lines\n")

    # Find where the class ends (around line 2067)
    print("[3/5] Analyzing structure...")
    class_end_line = None
    main_start_line = None

    for i, line in enumerate(lines):
        if line.startswith('def main():'):
            main_start_line = i
            break

    if not main_start_line:
        print("[ERROR] Could not find main() function")
        return False

    # Find the last non-empty, non-comment line before main()
    for i in range(main_start_line - 1, 0, -1):
        line = lines[i].strip()
        if line and not line.startswith('#') and not line.startswith('='):
            class_end_line = i + 1  # Insert after this line
            break

    print(f"[INFO] Class ends at line {class_end_line + 1}")
    print(f"[INFO] main() starts at line {main_start_line + 1}\n")

    # Find methods inside main() that should be in the class
    print("[4/5] Finding misplaced methods...")
    misplaced_methods = []
    current_method_start = None
    current_method_name = None
    indent_level = 0

    for i in range(main_start_line, len(lines)):
        line = lines[i]

        # Check for method definition (indented with 4-5 spaces + "def _create_")
        if re.match(r'^    def (_create_\w+)\(self\):', line):
            # If we were tracking a previous method, save it
            if current_method_start is not None:
                misplaced_methods.append({
                    'name': current_method_name,
                    'start': current_method_start,
                    'end': i - 1
                })

            # Start tracking this method
            match = re.match(r'^    def (_create_\w+)\(self\):', line)
            current_method_name = match.group(1)
            current_method_start = i
            indent_level = 1

        # Check for end of method (another def at same level or end of file)
        elif current_method_start is not None:
            if re.match(r'^    def ', line) or line.startswith('if __name__'):
                # End of current method
                misplaced_methods.append({
                    'name': current_method_name,
                    'start': current_method_start,
                    'end': i - 1
                })
                current_method_start = None
                current_method_name = None

    # Handle last method if any
    if current_method_start is not None:
        # Find the actual end by looking for the last indented line
        for i in range(len(lines) - 1, current_method_start, -1):
            if lines[i].strip() and lines[i].startswith('        '):
                misplaced_methods.append({
                    'name': current_method_name,
                    'start': current_method_start,
                    'end': i
                })
                break

    print(f"[FOUND] {len(misplaced_methods)} misplaced methods:")
    for method in misplaced_methods:
        print(f"  - {method['name']} (lines {method['start']+1}-{method['end']+1})")
    print()

    if not misplaced_methods:
        print("[INFO] No misplaced methods found - file may already be fixed")
        return True

    # Extract method bodies
    print("[5/5] Restructuring file...")
    method_bodies = {}
    for method in misplaced_methods:
        method_lines = lines[method['start']:method['end']+1]
        method_bodies[method['name']] = method_lines

    # Build new file content
    new_lines = []

    # Part 1: Everything up to class end
    new_lines.extend(lines[:class_end_line])

    # Part 2: Add the methods to the class (with proper indentation already)
    for method_name in sorted(method_bodies.keys()):
        new_lines.append("\n")
        new_lines.extend(method_bodies[method_name])

    # Part 3: Add comment separator and main() function
    # Skip the old methods in main() by jumping past them
    last_method_end = max(m['end'] for m in misplaced_methods)

    # Find where to continue (after the last method)
    continuation_line = last_method_end + 1
    while continuation_line < len(lines) and lines[continuation_line].strip() == '':
        continuation_line += 1

    # Add separator comment if not already there
    if not any('STANDALONE LAUNCH' in line for line in new_lines[-5:]):
        new_lines.append("\n")
        new_lines.append("# " + "=" * 82 + "\n")
        new_lines.append("# STANDALONE LAUNCH (for testing)\n")
        new_lines.append("# " + "=" * 82 + "\n")
        new_lines.append("\n")

    # Part 4: Add main() function and everything after
    # Find where main() should start (skip the method definitions)
    for i in range(continuation_line, len(lines)):
        if lines[i].startswith('def main():') or lines[i].startswith('if __name__'):
            new_lines.extend(lines[i:])
            break

    # Write the fixed file
    print(f"[WRITE] Writing {len(new_lines)} lines...")
    with open(it_portal_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"[OK] File restructured successfully\n")

    print("=" * 70)
    print("IT PORTAL STRUCTURE FIX COMPLETE")
    print("=" * 70)
    print(f"\n[SUCCESS] Methods moved into ITPortal class")
    print(f"Backup saved to: {backup_path.name}")
    print(f"Original lines: {len(lines)}")
    print(f"New lines: {len(new_lines)}")
    print(f"Methods moved: {len(misplaced_methods)}\n")

    return True

if __name__ == "__main__":
    success = fix_it_portal_structure()
    exit(0 if success else 1)
