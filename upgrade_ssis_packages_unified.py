#!/usr/bin/env python3
"""
SSIS Package Modernization Tool
Upgrades SSIS .dtsx packages to modern format by:
1. Simplifying ExecutableType and CreationName attributes
2. Upgrading component class IDs from legacy DTS to Microsoft format

Usage:
    python upgrade_ssis_packages_unified.py [options] <path>

Options:
    --backup            Create .bak backup files before modifying
    --dry-run           Show what would be changed without making modifications
    --recursive         Process all .dtsx files in subdirectories
    --verbose           Show detailed processing information
    --executable-only   Only upgrade ExecutableType/CreationName attributes
    --classid-only      Only upgrade component class IDs

Examples:
    # Upgrade single file with backup (both types of upgrades)
    python upgrade_ssis_packages_unified.py --backup mypackage.dtsx

    # Upgrade all packages in directory (dry run)
    python upgrade_ssis_packages_unified.py --dry-run --recursive /path/to/packages/

    # Process only ExecutableType attributes
    python upgrade_ssis_packages_unified.py --executable-only --backup --recursive .
    
    # Process only component class IDs
    python upgrade_ssis_packages_unified.py --classid-only --backup --recursive .
"""

import os
import sys
import re
import shutil
import argparse
from pathlib import Path
from typing import Dict, List, Tuple


# Mapping of ExecutableType patterns to simplified names
EXECUTABLE_TYPE_MAPPINGS = [
    # Pipeline Task - GUID format (case-insensitive)
    (r'\{5918251B-2970-45A4-AB5F-01C3C588FE5A\}', 'Microsoft.Pipeline'),
    
    # Pipeline Task - matches SSIS.Pipeline, SSIS.Pipeline.2, SSIS.Pipeline.3, etc.
    (r'SSIS\.Pipeline(\.\d+)?', 'Microsoft.Pipeline'),
    
    # ExecutePackage Task - matches SSIS.ExecutePackageTask.3, etc.
    (r'SSIS\.ExecutePackageTask(\.\d+)?', 'Microsoft.ExecutePackageTask'),
    
    # Package - matches SSIS.Package.3, etc.
    (r'SSIS\.Package(\.\d+)?', 'Microsoft.Package'),
    
    # ExecuteProcess Task - matches Microsoft.SqlServer.ExecProcTask
    (r'[^"]*Microsoft\.SqlServer\.ExecProcTask[^"]*', 'Microsoft.ExecuteProcess'),
    
    # ExecuteSQL Task - matches Microsoft.SqlServer.SQLTask
    (r'[^"]*Microsoft\.SqlServer\.SQLTask[^"]*', 'Microsoft.ExecuteSQLTask'),
    
    # Expression Task - matches Microsoft.SqlServer.ExpressionTask
    (r'[^"]*Microsoft\.SqlServer\.ExpressionTask[^"]*', 'Microsoft.ExpressionTask'),
    
    # FileSystem Task - matches Microsoft.SqlServer.FileSystemTask
    (r'[^"]*Microsoft\.SqlServer\.FileSystemTask[^"]*', 'Microsoft.FileSystemTask'),
    
    # Script Task - matches Microsoft.SqlServer.ScriptTask
    (r'[^"]*Microsoft\.SqlServer\.ScriptTask[^"]*', 'Microsoft.ScriptTask'),
    
    # TransferDatabase Task - matches Microsoft.SqlServer.TransferDatabasesTask
    (r'[^"]*Microsoft\.SqlServer\.TransferDatabasesTask[^"]*', 'Microsoft.TransferDatabaseTask'),
    
    # DbMaintenanceReindex Task
    (r'[^"]*DbMaintenanceReindexTask[^"]*', 'Microsoft.DbMaintenanceReindexTask'),
    
    # DbMaintenanceShrink Task
    (r'[^"]*DbMaintenanceShrinkTask[^"]*', 'Microsoft.DbMaintenanceShrinkTask'),
    
    # DbMaintenanceTSQLExecute Task
    (r'[^"]*DbMaintenanceTSQLExecuteTask[^"]*', 'Microsoft.DbMaintenanceTSQLExecuteTask'),
    
    # DbMaintenanceUpdateStatistics Task
    (r'[^"]*DbMaintenanceUpdateStatisticsTask[^"]*', 'Microsoft.DbMaintenanceUpdateStatisticsTask'),
]


# Component ClassID mappings from legacy to modern format
COMPONENT_CLASSID_MAPPINGS = [
    # Managed Component Wrapper
    (r'DTS\.ManagedComponentWrapper\.3', 'Microsoft.ManagedComponentWrapper'),
    
    # Adapters - Destinations
    (r'DTSAdapter\.ExcelDestination\.3', 'Microsoft.ExcelDestination'),
    (r'DTSAdapter\.OLEDBDestination\.3', 'Microsoft.OLEDBDestination'),
    
    # Adapters - Sources
    (r'DTSAdapter\.ExcelSource\.3', 'Microsoft.ExcelSource'),
    (r'DTSAdapter\.FlatFileSource\.3', 'Microsoft.FlatFileSource'),
    (r'DTSAdapter\.OLEDBSource\.3', 'Microsoft.OLEDBSource'),
    
    # Transformations
    (r'DTSTransform\.Aggregate\.3', 'Microsoft.Aggregate'),
    (r'DTSTransform\.ConditionalSplit\.3', 'Microsoft.ConditionalSplit'),
    (r'DTSTransform\.DataConvert\.3', 'Microsoft.DataConvert'),
    (r'DTSTransform\.DerivedColumn\.3', 'Microsoft.DerivedColumn'),
    (r'DTSTransform\.Lookup\.3', 'Microsoft.Lookup'),
    (r'DTSTransform\.Merge\.3', 'Microsoft.Merge'),
    (r'DTSTransform\.MergeJoin\.3', 'Microsoft.MergeJoin'),
    (r'DTSTransform\.Multicast\.3', 'Microsoft.Multicast'),
    (r'DTSTransform\.OLEDBCommand\.3', 'Microsoft.OLEDBCommand'),
    (r'DTSTransform\.SCD\.3', 'Microsoft.SlowlyChangingDimension'),
    (r'DTSTransform\.Sort\.3', 'Microsoft.Sort'),
    (r'DTSTransform\.UnionAll\.3', 'Microsoft.UnionAll'),
]

# GUID-based Component ClassID mappings (case-insensitive)
GUID_COMPONENT_CLASSID_MAPPINGS = [
    # Transformations
    (r'\{5B201335-B360-485C-BB93-75C34E09B3D3\}', 'Microsoft.Aggregate'),  # Aggregate
    (r'\{7F88F654-4E20-4D14-84F4-AF9C925D3087\}', 'Microsoft.ConditionalSplit'),  # Conditional Split
    (r'\{62B1106C-7DB8-4EC8-ADD6-4C664DFFC54A\}', 'Microsoft.DataConvert'),  # Data Conversion
    (r'\{49928E82-9C4E-49F0-AABE-3812B82707EC\}', 'Microsoft.DerivedColumn'),  # Derived Column
    (r'\{671046B0-AA63-4C9F-90E4-C06E0B710CE3\}', 'Microsoft.Lookup'),  # Lookup
    (r'\{36E0E750-2510-4776-AA6E-17EAE84FD63E\}', 'Microsoft.Merge'),  # Merge
    (r'\{14D43A4F-D7BD-489D-829E-6DE35750CFE4\}', 'Microsoft.MergeJoin'),  # Merge Join
    (r'\{EC139FBC-694E-490B-8EA7-35690FB0F445\}', 'Microsoft.Multicast'),  # Multicast
    (r'\{93FFEC66-CBC8-4C7F-9C6A-CB1C17A7567D\}', 'Microsoft.OLEDBCommand'),  # OLE DB Command
    (r'\{25BBB0C5-369B-4303-B3DF-D0DC741DEE58\}', 'Microsoft.SlowlyChangingDimension'),  # Slowly Changing Dimension
    (r'\{5B1A3FF5-D366-4D75-AD1F-F19A36FCBEDB\}', 'Microsoft.Sort'),  # Sort
    (r'\{B594E9A8-4351-4939-891C-CFE1AB93E925\}', 'Microsoft.UnionAll'),  # Union All
    (r'\{874F7595-FB5F-40FF-96AF-FBFF8250E3EF\}', 'Microsoft.ManagedComponentWrapper'),  # Script Component / Managed Wrapper
    
    # Destinations
    (r'\{4ADA7EAA-136C-4215-8098-D7A7C27FC0D1\}', 'Microsoft.OLEDBDestination'),  # OLE DB Destination
    (r'\{8DA75FED-1B7C-407D-B2AD-2B24209CCCA4\}', 'Microsoft.FlatFileDestination'),  # Flat File Destination
    (r'\{C457FD7E-CE98-4C4B-AEFE-F3AE0044F181\}', 'Microsoft.RecordsetDestination'),  # Recordset Destination
    
    # Sources
    (r'\{165A526D-D5DE-47FF-96A6-F8274C19826B\}', 'Microsoft.OLEDBSource'),  # OLE DB Source
    (r'\{8C084929-27D1-479F-9641-ABB7CDADF1AC\}', 'Microsoft.ExcelSource'),  # Excel Source
    (r'\{D23FD76B-F51D-420F-BBCB-19CBF6AC1AB4\}', 'Microsoft.FlatFileSource'),  # Flat File Source
    (r'\{5918251B-2970-45A4-AB5F-01C3C588FE5A\}', 'Microsoft.OLEDBSource'),  # Alternative OLE DB Source GUID
    (r'\{98F16A65-E02F-4B0F-87D4-C217EA074619\}', 'Microsoft.ExcelSource'),  # Alternative Excel Source GUID
    (r'\{BD06A22E-BC69-4AF7-A69B-C44C2EF684BB\}', 'Microsoft.FlatFileSource'),  # Alternative Flat File Source GUID
]


class SSISPackageUpgrader:
    def __init__(self, verbose: bool = False, executable_only: bool = False, classid_only: bool = False):
        self.verbose = verbose
        self.executable_only = executable_only
        self.classid_only = classid_only
        self.stats = {
            'files_processed': 0,
            'files_modified': 0,
            'executable_replacements': 0,
            'classid_replacements': 0,
            'errors': 0
        }

    def log(self, message: str, force: bool = False):
        """Print message if verbose mode is enabled or force is True"""
        if self.verbose or force:
            print(message)

    def create_backup(self, file_path: Path) -> bool:
        """Create a backup of the file with .bak extension"""
        try:
            backup_path = file_path.with_suffix(file_path.suffix + '.bak')
            shutil.copy2(file_path, backup_path)
            self.log(f"  ✓ Backup created: {backup_path.name}")
            return True
        except Exception as e:
            print(f"  ✗ Error creating backup: {e}")
            return False

    def simplify_executable_types(self, content: str) -> Tuple[str, int]:
        """
        Simplify ExecutableType and CreationName attributes by replacing
        assembly-qualified names with simple names
        Returns: (updated_content, count_of_replacements)
        """
        replacements = 0
        updated_content = content
        
        for pattern, new_name in EXECUTABLE_TYPE_MAPPINGS:
            # Find all matches for this pattern in both DTS:CreationName and DTS:ExecutableType
            for attribute in ['DTS:CreationName', 'DTS:ExecutableType']:
                # Match the attribute with the old value
                attr_pattern = f'{attribute}="({pattern})"'
                
                def replace_match(match):
                    nonlocal replacements
                    replacements += 1
                    return f'{attribute}="{new_name}"'
                
                # Use case-insensitive matching for GUID patterns
                if pattern.startswith(r'\{'):
                    updated_content = re.sub(attr_pattern, replace_match, updated_content, flags=re.IGNORECASE)
                else:
                    updated_content = re.sub(attr_pattern, replace_match, updated_content)
        
        return updated_content, replacements

    def upgrade_component_classids(self, content: str) -> Tuple[str, int]:
        """
        Upgrade component class IDs from legacy DTS format to modern Microsoft format
        Returns: (updated_content, count_of_replacements)
        """
        replacements = 0
        updated_content = content
        
        # First, handle string-based patterns (DTS*, DTSAdapter*, DTSTransform*)
        for pattern, new_value in COMPONENT_CLASSID_MAPPINGS:
            # Match componentClassID="..." attribute
            attr_pattern = f'componentClassID="({pattern})"'
            
            def replace_match(match):
                nonlocal replacements
                replacements += 1
                return f'componentClassID="{new_value}"'
            
            updated_content = re.sub(attr_pattern, replace_match, updated_content)
        
        # Then, handle GUID-based patterns (case-insensitive)
        for guid_pattern, new_value in GUID_COMPONENT_CLASSID_MAPPINGS:
            # Match componentClassID="{GUID}" attribute (case-insensitive)
            attr_pattern = f'componentClassID="({guid_pattern})"'
            
            def replace_guid_match(match):
                nonlocal replacements
                replacements += 1
                return f'componentClassID="{new_value}"'
            
            updated_content = re.sub(attr_pattern, replace_guid_match, updated_content, flags=re.IGNORECASE)
        
        return updated_content, replacements

    def upgrade_package(self, file_path: Path, dry_run: bool = False) -> bool:
        """Upgrade a single SSIS package file"""
        self.log(f"\nProcessing: {file_path}", force=True)
        self.stats['files_processed'] += 1
        
        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            updated_content = content
            total_replacements = 0
            
            # Perform executable type upgrades unless classid_only mode
            if not self.classid_only:
                updated_content, exec_replacements = self.simplify_executable_types(updated_content)
                self.stats['executable_replacements'] += exec_replacements
                total_replacements += exec_replacements
                if exec_replacements > 0:
                    self.log(f"  Found {exec_replacements} ExecutableType/CreationName attribute(s) to simplify")
            
            # Perform component class ID upgrades unless executable_only mode
            if not self.executable_only:
                updated_content, classid_replacements = self.upgrade_component_classids(updated_content)
                self.stats['classid_replacements'] += classid_replacements
                total_replacements += classid_replacements
                if classid_replacements > 0:
                    self.log(f"  Found {classid_replacements} component class ID(s) to upgrade")
            
            if total_replacements == 0:
                self.log("  No updates needed")
                return True
            
            if dry_run:
                self.log(f"  [DRY RUN] Would make {total_replacements} total change(s)")
                return True
            
            # Write the updated content
            if updated_content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                self.stats['files_modified'] += 1
                self.log(f"  ✓ Successfully updated {total_replacements} attribute(s)", force=True)
                return True
            else:
                self.log("  No changes made")
                return True
                
        except Exception as e:
            print(f"  ✗ Error processing file: {e}")
            self.stats['errors'] += 1
            return False

    def process_path(self, path: Path, recursive: bool = False, backup: bool = False, dry_run: bool = False):
        """Process a file or directory"""
        if path.is_file():
            if path.suffix.lower() == '.dtsx':
                if backup and not dry_run:
                    if not self.create_backup(path):
                        return
                self.upgrade_package(path, dry_run)
            else:
                print(f"Skipping non-DTSX file: {path}")
        elif path.is_dir():
            pattern = '**/*.dtsx' if recursive else '*.dtsx'
            dtsx_files = list(path.glob(pattern))
            
            if not dtsx_files:
                print(f"No .dtsx files found in {path}")
                return
            
            print(f"Found {len(dtsx_files)} .dtsx file(s) to process")
            
            for file_path in dtsx_files:
                if backup and not dry_run:
                    if not self.create_backup(file_path):
                        continue
                self.upgrade_package(file_path, dry_run)
        else:
            print(f"Error: Path not found: {path}")

    def print_summary(self, dry_run: bool = False):
        """Print processing summary"""
        print("\n" + "="*60)
        if dry_run:
            print("DRY RUN SUMMARY")
        else:
            print("PROCESSING SUMMARY")
        print("="*60)
        print(f"Files processed:                {self.stats['files_processed']}")
        print(f"Files modified:                 {self.stats['files_modified']}")
        
        if not self.classid_only:
            print(f"ExecutableType upgrades:        {self.stats['executable_replacements']}")
        if not self.executable_only:
            print(f"Component ClassID upgrades:     {self.stats['classid_replacements']}")
        
        total = self.stats['executable_replacements'] + self.stats['classid_replacements']
        print(f"Total upgrades:                 {total}")
        print(f"Errors encountered:             {self.stats['errors']}")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description='Modernize SSIS .dtsx packages (ExecutableType and ComponentClassID attributes)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('path', help='Path to .dtsx file or directory containing .dtsx files')
    parser.add_argument('--backup', '-b', action='store_true',
                       help='Create .bak backup files before modifying')
    parser.add_argument('--dry-run', '-n', action='store_true',
                       help='Show what would be changed without making modifications')
    parser.add_argument('--recursive', '-r', action='store_true',
                       help='Process all .dtsx files in subdirectories')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed processing information')
    parser.add_argument('--executable-only', action='store_true',
                       help='Only upgrade ExecutableType/CreationName attributes')
    parser.add_argument('--classid-only', action='store_true',
                       help='Only upgrade component class IDs')
    
    args = parser.parse_args()
    
    # Validate mutually exclusive options
    if args.executable_only and args.classid_only:
        print("Error: --executable-only and --classid-only cannot be used together")
        sys.exit(1)
    
    path = Path(args.path)
    
    if not path.exists():
        print(f"Error: Path not found: {path}")
        sys.exit(1)
    
    print("SSIS Package Modernization Tool")
    print("="*60)
    if args.executable_only:
        print("Mode: ExecutableType/CreationName upgrades only")
    elif args.classid_only:
        print("Mode: Component ClassID upgrades only")
    else:
        print("Mode: Full upgrade (ExecutableType + Component ClassID)")
    
    if args.dry_run:
        print("DRY RUN: No files will be modified")
    if args.backup and not args.dry_run:
        print("Backup: .bak files will be created")
    print("="*60)
    print()
    
    upgrader = SSISPackageUpgrader(
        verbose=args.verbose,
        executable_only=args.executable_only,
        classid_only=args.classid_only
    )
    upgrader.process_path(path, recursive=args.recursive, backup=args.backup, dry_run=args.dry_run)
    upgrader.print_summary(dry_run=args.dry_run)
    
    if args.dry_run:
        print("\nNo files were modified. Run without --dry-run to apply changes.")


if __name__ == '__main__':
    main()
