# SSIS Package Modernization Tool

A unified Python utility to modernize SSIS (SQL Server Integration Services) `.dtsx` package files by:
1. **Simplifying ExecutableType and CreationName attributes** - Removes assembly-qualified names and version information
2. **Upgrading component class IDs** - Converts legacy DTS component class IDs to modern Microsoft format

## What It Does

This script performs comprehensive modernization of SSIS packages, converting them to current standards. This modernization helps:

- **Reduce file complexity**: Removes long assembly names with version numbers and public key tokens
- **Improve readability**: Simplified names are easier to understand and maintain
- **Modernize legacy packages**: Updates SQL Server 2008/2012/2014 packages to current standards
- **Ensure consistency**: Standardizes naming across all your SSIS packages
- **Update component references**: Modernizes data flow component class IDs

## Transformations

### ExecutableType and CreationName Upgrades

The script performs the following conversions:

| Old Format | New Format |
|------------|------------|
| `SSIS.Pipeline.3` | `Microsoft.Pipeline` |
| `SSIS.ExecutePackageTask.3` | `Microsoft.ExecutePackageTask` |
| `SSIS.Package.3` | `Microsoft.Package` |
| `Microsoft.SqlServer.Dts.Tasks.ExecuteProcess.ExecuteProcess, Microsoft.SqlServer.ExecProcTask, Version=11.0.0.0, Culture=neutral, PublicKeyToken=89845dcd8080cc91` | `Microsoft.ExecuteProcess` |
| `Microsoft.SqlServer.Dts.Tasks.ExecuteSQLTask.ExecuteSQLTask, Microsoft.SqlServer.SQLTask, Version=11.0.0.0, ...` | `Microsoft.ExecuteSQLTask` |
| `Microsoft.SqlServer.Dts.Tasks.FileSystemTask.FileSystemTask, Microsoft.SqlServer.FileSystemTask, Version=11.0.0.0, ...` | `Microsoft.FileSystemTask` |
| `Microsoft.SqlServer.Dts.Tasks.ScriptTask.ScriptTask, Microsoft.SqlServer.ScriptTask, Version=11.0.0.0, ...` | `Microsoft.ScriptTask` |

And many more task types including Expression, TransferDatabase, and Database Maintenance tasks.

### Component Class ID Upgrades

The script also upgrades data flow component class IDs:

| Old Format | New Format |
|------------|------------|
| `DTS.ManagedComponentWrapper.3` | `Microsoft.ManagedComponentWrapper` |
| `DTSAdapter.OLEDBSource.3` | `Microsoft.OLEDBSource` |
| `DTSAdapter.OLEDBDestination.3` | `Microsoft.OLEDBDestination` |
| `DTSAdapter.ExcelSource.3` | `Microsoft.ExcelSource` |
| `DTSAdapter.ExcelDestination.3` | `Microsoft.ExcelDestination` |
| `DTSAdapter.FlatFileSource.3` | `Microsoft.FlatFileSource` |
| `DTSTransform.Lookup.3` | `Microsoft.Lookup` |
| `DTSTransform.Sort.3` | `Microsoft.Sort` |
| `DTSTransform.Aggregate.3` | `Microsoft.Aggregate` |
| `DTSTransform.MergeJoin.3` | `Microsoft.MergeJoin` |
| `DTSTransform.ConditionalSplit.3` | `Microsoft.ConditionalSplit` |
| `DTSTransform.DerivedColumn.3` | `Microsoft.DerivedColumn` |
| `DTSTransform.DataConvert.3` | `Microsoft.DataConvert` |
| `DTSTransform.OLEDBCommand.3` | `Microsoft.OLEDBCommand` |
| `DTSTransform.UnionAll.3` | `Microsoft.UnionAll` |

And more transformation components including Merge, Multicast, and Slowly Changing Dimension.

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only Python standard library)

## Installation

No installation needed! Just download the script:

```bash
# The script is ready to use
python upgrade_ssis_packages_unified.py --help
```

## Usage

### Basic Usage

```bash
# Preview changes on a single file (dry run)
python upgrade_ssis_packages_unified.py --dry-run mypackage.dtsx

# Apply all changes to a single file with backup
python upgrade_ssis_packages_unified.py --backup mypackage.dtsx

# Process all packages in current directory
python upgrade_ssis_packages_unified.py --backup --recursive .

# Only upgrade ExecutableType attributes
python upgrade_ssis_packages_unified.py --executable-only --backup --recursive .

# Only upgrade component class IDs
python upgrade_ssis_packages_unified.py --classid-only --backup --recursive .
```

### Command-Line Options

| Option | Description |
|--------|-------------|
| `path` | Path to `.dtsx` file or directory containing `.dtsx` files (required) |
| `--backup`, `-b` | Create `.bak` backup files before modifying |
| `--dry-run`, `-n` | Show what would be changed without making modifications |
| `--recursive`, `-r` | Process all `.dtsx` files in subdirectories |
| `--verbose`, `-v` | Show detailed processing information |
| `--executable-only` | Only upgrade ExecutableType/CreationName attributes |
| `--classid-only` | Only upgrade component class IDs |

### Examples

**1. Test on a single file first:**
```bash
python upgrade_ssis_packages_unified.py --dry-run --verbose MyPackage.dtsx
```

**2. Apply changes with backup:**
```bash
python upgrade_ssis_packages_unified.py --backup MyPackage.dtsx
```

**3. Process entire directory recursively:**
```bash
python upgrade_ssis_packages_unified.py --backup --recursive ./SSIS_Packages/
```

**4. Only upgrade ExecutableType attributes:**
```bash
python upgrade_ssis_packages_unified.py --executable-only --backup --recursive .
```

**5. Only upgrade component class IDs:**
```bash
python upgrade_ssis_packages_unified.py --classid-only --backup --recursive .
```

**6. Verbose output to see all changes:**
```bash
python upgrade_ssis_packages_unified.py --backup --verbose --recursive .
```

## Output

The script provides a summary after execution:

```
SSIS Package Modernization Tool
============================================================
Mode: Full upgrade (ExecutableType + Component ClassID)
Backup: .bak files will be created
============================================================

Found 229 .dtsx file(s) to process

Processing: MyPackage.dtsx
  Found 6 ExecutableType/CreationName attribute(s) to simplify
  Found 3 component class ID(s) to upgrade
  ✓ Successfully updated 9 attribute(s)

Processing: MyPackage2.dtsx
  Found 2 ExecutableType/CreationName attribute(s) to simplify
  ✓ Successfully updated 2 attribute(s)

============================================================
PROCESSING SUMMARY
============================================================
Files processed:                229
Files modified:                 185
ExecutableType upgrades:        3039
Component ClassID upgrades:     1247
Total upgrades:                 4286
Errors encountered:             0
============================================================
```

## Safety Features

### Backup Creation
Using the `--backup` flag creates `.bak` files before any modifications:
```
MyPackage.dtsx      (modified)
MyPackage.dtsx.bak  (original backup)
```

### Dry Run Mode
The `--dry-run` flag lets you preview all changes without modifying any files:
```bash
python upgrade_ssis_packages_unified.py --dry-run --verbose MyPackage.dtsx
```

### Mode Selection
Choose specific upgrade modes for targeted processing:
- Default: Performs both ExecutableType and component class ID upgrades
- `--executable-only`: Only upgrades ExecutableType/CreationName attributes
- `--classid-only`: Only upgrades component class IDs

### Selective Processing
The script only processes `.dtsx` files and skips non-SSIS files automatically.

## Supported Task Types

The script handles these SSIS components:

**Control Flow Tasks:**
- Data Flow: Pipeline tasks
- ExecutePackage tasks
- ExecuteProcess, ExecuteSQL, Script tasks
- File Operations: FileSystem
- Expression tasks
- Database Tasks: TransferDatabase
- Maintenance Tasks: Reindex, Shrink, T-SQL Execute, Update Statistics

**Data Flow Components:**
- Sources: OLE DB, Excel, Flat File
- Destinations: OLE DB, Excel
- Transformations: Lookup, Sort, Aggregate, Merge Join, Conditional Split, Derived Column, Data Conversion, Union All, Multicast, OLE DB Command, Slowly Changing Dimension
- Managed Component Wrapper

## Restoring from Backup

If you need to restore original files:

### Single File
```bash
cp MyPackage.dtsx.bak MyPackage.dtsx
```

### All Files in Directory
```bash
# Restore all backups
find . -name "*.dtsx.bak" -exec sh -c 'cp "$1" "${1%.bak}"' _ {} \;
```

### Remove Backups After Verification
```bash
# Remove all .bak files once you're satisfied
find . -name "*.dtsx.bak" -delete
```

## Troubleshooting

### "No .dtsx files found"
- Verify you're in the correct directory
- Check file extensions are `.dtsx` (case-insensitive)
- Use `--recursive` if files are in subdirectories

### "Error processing file"
- Ensure files are not locked by Visual Studio or SQL Server
- Check file permissions (read/write access required)
- Verify XML is well-formed (not corrupted)

### Changes not appearing
- Confirm you removed the `--dry-run` flag
- Check the summary output for "Files modified" count
- Use `--verbose` to see detailed processing

## Best Practices

1. **Always test first**: Use `--dry-run` before making changes
2. **Create backups**: Always use `--backup` for the first run
3. **Version control**: Commit your packages to Git before running the script
4. **Test packages**: Test modified packages in a development environment
5. **Batch processing**: Process all packages at once for consistency

## Version Control Integration

### With Git:

```bash
# Before running the script
git status  # Ensure working directory is clean
git commit -am "Backup before SSIS modernization"

# Run the script
python upgrade_ssis_packages_unified.py --recursive .

# Review changes
git diff

# Commit if satisfied
git commit -am "Modernize SSIS packages: ExecutableTypes and Component ClassIDs"
```

## Technical Details

### How It Works

1. Scans for `.dtsx` files in specified path(s)
2. Reads each file as XML text
3. Uses regex patterns to find:
   - Assembly-qualified names in `DTS:CreationName` and `DTS:ExecutableType` attributes
   - Legacy component class IDs in `componentClassID` attributes
4. Replaces matches with simplified/modern names
5. Writes updated content back to file (with optional backup)

### Upgrade Types

**ExecutableType Upgrades:**
- Targets `DTS:CreationName` and `DTS:ExecutableType` attributes
- Removes assembly version information and public key tokens
- Converts SSIS.* patterns to Microsoft.* format

**Component ClassID Upgrades:**
- Targets `componentClassID` attributes in data flow components
- Converts DTS*/DTSAdapter*/DTSTransform* patterns to Microsoft.* format
- Maintains component functionality while modernizing references

### File Format

SSIS `.dtsx` files are XML-based. The script uses text processing rather than XML parsing to preserve formatting and avoid any potential XML namespace issues.

### Performance

- Processes hundreds of files in seconds
- Memory-efficient (processes one file at a time)
- No external dependencies or database connections needed

## License

This script is provided as-is for SSIS package modernization purposes.

## Support

For issues or questions:
1. Run with `--dry-run --verbose` to see detailed processing
2. Check that your `.dtsx` files are valid XML
3. Verify you have read/write permissions on the files

## Related Tools

You may also want to:
- Use SQL Server Data Tools (SSDT) for full package upgrades
- Consider SQL Server Integration Services Projects in Visual Studio
- Review Microsoft's SSIS documentation for migration best practices
