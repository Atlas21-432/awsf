#!/usr/bin/env python3
"""
AWSF - AWS Fuzzy Finder
=======================

A powerful fuzzy search tool for AWS resources across multiple services.

Features:
- Fuzzy search with instant results across multiple AWS services
- Service-specific searches (e.g., "lambda payment", "s3 bucket", "sqs queue")
- Environment indicators (🟢 PROD / 🟡 STAGE / 🔵 DEV)  
- Multiple access methods: CLI, GUI integration, keyboard shortcuts
- Quick actions: open in AWS Console, copy URL to clipboard
- Configurable service toggles and settings

Supported Services:
- Lambda functions
- S3 buckets
- SQS queues 
- Kinesis streams
- DynamoDB tables
- RDS instances/clusters
- API Gateway APIs

Usage:
    awsf                        # Interactive mode - all services
    awsf lambda payment         # Search Lambda functions for "payment"
    awsf s3 media              # Search S3 buckets for "media"
    awsf sqs queue             # Search SQS queues for "queue"
    awsf --settings            # Open settings menu
"""

import json
import sys
import subprocess
import os
from difflib import get_close_matches

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
RESOURCES_FILE = os.path.join(PROJECT_ROOT, "data", "aws_resources.json")
SETTINGS_FILE = os.path.join(PROJECT_ROOT, "config", "settings.json")
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config", "config.json")

# Service mappings and icons
SERVICE_CONFIG = {
    'lambda': {'icon': 'λ', 'color': '🟡', 'name': 'Lambda'},
    's3': {'icon': '🪣', 'color': '🟢', 'name': 'S3'},
    'sqs': {'icon': '📬', 'color': '🔵', 'name': 'SQS'},
    'kinesis': {'icon': '🌊', 'color': '🟣', 'name': 'Kinesis'},
    'dynamodb': {'icon': '🗄️', 'color': '🟠', 'name': 'DynamoDB'},
    'rds': {'icon': '🗃️', 'color': '🔴', 'name': 'RDS'},
    'apigateway': {'icon': '🚪', 'color': '⚫', 'name': 'API Gateway'}
}

def load_config():
    """Load configuration from JSON file"""
    default_config = {
        "aws_region": "us-east-1",
        "aws_profile": None,
        "console_base_url": "https://console.aws.amazon.com"
    }
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # Merge with defaults
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            return config
    except (FileNotFoundError, json.JSONDecodeError):
        # Create default config file
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        save_config(default_config)
        return default_config

def save_config(config):
    """Save configuration to JSON file"""
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    except (OSError, IOError) as e:
        print(f"❌ Error saving config: {e}")

def get_service_display(service, resource_type=None):
    """Get display info for a service"""
    config = SERVICE_CONFIG.get(service, {'icon': '❓', 'color': '⚪', 'name': service.upper()})
    if resource_type and resource_type in ['cluster']:
        return f"{config['icon']} {config['name']} Cluster"
    return f"{config['icon']} {config['name']}"

def get_environment_indicator(resource_name):
    """Get environment indicator based on resource name"""
    name_lower = resource_name.lower()
    if any(env in name_lower for env in ['prod', 'production']):
        return "🟢 PROD"
    elif any(env in name_lower for env in ['stag', 'staging', 'stage']):
        return "🟡 STAGE"
    elif any(env in name_lower for env in ['dev', 'development']):
        return "🔵 DEV"
    elif any(env in name_lower for env in ['test', 'testing']):
        return "🟣 TEST"
    else:
        return "⚪ OTHER"

def load_aws_resources():
    """Load AWS resources from JSON file"""
    try:
        with open(RESOURCES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {RESOURCES_FILE} not found")
        print("💡 Run: python3 scripts/populate_resources.py")
        return {}
    except json.JSONDecodeError:
        print(f"❌ Error: {RESOURCES_FILE} is not valid JSON")
        return {}
    except (OSError, IOError) as e:
        print(f"❌ Error loading AWS resources: {e}")
        return {}

def load_settings():
    """Load settings from JSON file"""
    default_settings = {
        "enabled_services": list(SERVICE_CONFIG.keys())
    }
    
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            # Ensure all services are present in settings
            if "enabled_services" not in settings:
                settings["enabled_services"] = list(SERVICE_CONFIG.keys())
            return settings
    except (FileNotFoundError, json.JSONDecodeError):
        # Create default settings file
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        save_settings(default_settings)
        return default_settings

def save_settings(settings):
    """Save settings to JSON file"""
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
    except (OSError, IOError) as e:
        print(f"❌ Error saving settings: {e}")

def filter_by_service(resources, service_filter=None):
    """Filter resources by service type and enabled services"""
    settings = load_settings()
    enabled_services = set(settings.get("enabled_services", SERVICE_CONFIG.keys()))
    
    # First filter by enabled services
    filtered_resources = {name: resource for name, resource in resources.items() 
                         if resource.get('service', '').lower() in enabled_services}
    
    # Then filter by specific service if provided
    if service_filter:
        service_filter = service_filter.lower()
        filtered_resources = {name: resource for name, resource in filtered_resources.items() 
                            if resource.get('service', '').lower() == service_filter}
    
    return filtered_resources

def prepare_resource_data(resources, service_filter=None):
    """Prepare resource data for fzf with service indicators and metadata"""
    if not resources:
        return []
    
    # Filter by service if specified
    if service_filter:
        resources = filter_by_service(resources, service_filter)
    
    formatted_lines = []
    for name, resource in resources.items():
        service = resource.get('service', 'unknown')
        resource_type = resource.get('type', 'unknown')
        url = resource.get('url', '')
        
        # Get display components
        service_display = get_service_display(service, resource_type)
        env_indicator = get_environment_indicator(name)
        
        # Create searchable line with metadata
        line = f"{name} | {service_display} | {env_indicator} | {url}"
        formatted_lines.append(line)
    
    return sorted(formatted_lines)

def parse_search_query(args):
    """Parse command line arguments to extract service and search terms"""
    if not args:
        return None, ""
    
    # Check if first argument is a service name
    first_arg = args[0].lower()
    valid_services = list(SERVICE_CONFIG.keys())
    
    if first_arg in valid_services:
        service = first_arg
        search_terms = " ".join(args[1:]) if len(args) > 1 else ""
        return service, search_terms
    else:
        # No service specified, search all services
        search_terms = " ".join(args)
        return None, search_terms

def run_fzf_search(service_filter=None):
    """Run interactive fuzzy search with fzf"""
    resources = load_aws_resources()
    resource_data = prepare_resource_data(resources, service_filter)
    
    if not resource_data:
        if service_filter:
            print(f"❌ No {service_filter.upper()} resources found")
        else:
            print("❌ No AWS resources found")
        return
    
    # Build header text
    if service_filter:
        header = f"🔍 Search {SERVICE_CONFIG[service_filter]['name']} Resources (Enter=Open, Ctrl+C=Copy URL)"
        prompt = f"{SERVICE_CONFIG[service_filter]['icon']} Search: "
    else:
        header = "🔍 Search AWS Resources (Enter=Open, Ctrl+C=Copy URL)"
        prompt = "☁️ Search: "
    
    # fzf command with advanced options and better spacing
    fzf_cmd = [
        'fzf',
        '--height=80%',           # Increase height for better layout
        '--layout=default',       # Use default layout (prompt at top)
        '--border',
        '--margin=2,4',           # Add margin (vertical, horizontal)
        '--padding=1',            # Add padding inside border
        '--info=inline',          # Show info inline to save space
        '--preview-window=down:8:wrap:border',  # Preview at bottom with border
        '--preview=echo "╭─── 📋 Resource Details ───╮\n│ 🏷️  Name: {1}\n│ 🔧 Service: {2}\n│ 🌍 Environment: {3}\n│ 🔗 Console: {4}\n│\n│ 💡 Press Enter to open in AWS Console\n│ 💡 Press Ctrl+C to copy URL to clipboard\n╰─────────────────────────────╯"',
        f'--header={header}',
        f'--prompt={prompt}',
        '--delimiter=|',
        '--with-nth=1,2,3',  # Show name, service, and environment
        '--bind=ctrl-c:execute(echo {4} | pbcopy)+abort',  # Copy URL on Ctrl+C
        '--bind=enter:execute(open {4})',  # Open URL on Enter
        '--ansi'
    ]
    
    try:
        # Run fzf with resource data
        process = subprocess.Popen(
            fzf_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        input_data = '\n'.join(resource_data)
        stdout, _ = process.communicate(input=input_data)
        
        if process.returncode == 0 and stdout.strip():
            # Extract URL from selected line
            selected_line = stdout.strip()
            parts = selected_line.split(' | ')
            if len(parts) >= 4:
                resource_name = parts[0]
                service_info = parts[1]
                url = parts[3]
                subprocess.run(['open', url], check=False)
                print(f"🚀 Opening {resource_name} ({service_info}) in AWS Console")
        elif process.returncode == 130:  # Ctrl+C pressed
            print("📋 URL copied to clipboard")
            
    except KeyboardInterrupt:
        print("\n👋 Search cancelled")
    except FileNotFoundError:
        print("❌ fzf not found. Please install with: brew install fzf")
    except (OSError, subprocess.SubprocessError) as e:
        print(f"❌ Error running search: {e}")

def search_with_query(query, service_filter=None):
    """Search with a specific query"""
    resources = load_aws_resources()
    
    if not resources:
        return
    
    # Filter by service if specified
    if service_filter:
        resources = filter_by_service(resources, service_filter)
        
    # Find matches
    query_lower = query.lower()
    matches = [(name, resource) for name, resource in resources.items() 
               if query_lower in name.lower()]
    
    if not matches:
        service_text = f" {service_filter.upper()}" if service_filter else ""
        print(f"❌ No{service_text} resources found matching: '{query}'")
        
        # Show suggestions
        all_names = list(resources.keys())
        suggestions = get_close_matches(query, all_names, n=3, cutoff=0.3)
        if suggestions:
            print("💡 Did you mean:")
            for suggestion in suggestions:
                resource = resources[suggestion]
                service_display = get_service_display(resource['service'], resource.get('type'))
                print(f"   • {suggestion} ({service_display})")
        return
    
    if len(matches) == 1:
        # Open directly
        name, resource = matches[0]
        url = resource.get('url', '')
        if url:
            subprocess.run(['open', url], check=False)
            service_display = get_service_display(resource['service'], resource.get('type'))
            env = get_environment_indicator(name)
            print(f"🚀 Opening {name} ({service_display}) {env} in AWS Console")
        else:
            print(f"❌ No URL available for {name}")
    else:
        # Use fzf for selection with filtered results
        run_fzf_for_matches(matches, service_filter)

def run_fzf_for_matches(matches, service_filter):
    """Run fzf for multiple matches"""
    resource_data = []
    for name, resource in matches:
        service = resource.get('service', 'unknown')
        resource_type = resource.get('type', 'unknown')
        url = resource.get('url', '')
        
        service_display = get_service_display(service, resource_type)
        env_indicator = get_environment_indicator(name)
        
        line = f"{name} | {service_display} | {env_indicator} | {url}"
        resource_data.append(line)
    
    # Build header for multiple matches
    service_text = f" {service_filter.upper()}" if service_filter else ""
    header = f"🔍 Found {len(matches)}{service_text} matches - Select one"
    
    fzf_cmd = [
        'fzf',
        '--height=80%',
        '--layout=default',
        '--border',
        '--margin=2,4',
        '--padding=1',
        '--info=inline',
        '--preview-window=down:8:wrap:border',
        '--preview=echo "╭─── 📋 Resource Details ───╮\n│ 🏷️  Name: {1}\n│ 🔧 Service: {2}\n│ 🌍 Environment: {3}\n│ 🔗 Console: {4}\n│\n│ 💡 Press Enter to open in AWS Console\n│ 💡 Press Ctrl+C to copy URL to clipboard\n╰─────────────────────────────╯"',
        f'--header={header}',
        '--prompt=☁️ Select: ',
        '--delimiter=|',
        '--with-nth=1,2,3',
        '--bind=ctrl-c:execute(echo {4} | pbcopy)+abort',
        '--bind=enter:execute(open {4})',
        '--ansi'
    ]
    
    try:
        process = subprocess.Popen(
            fzf_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True
        )
        
        input_data = '\n'.join(resource_data)
        stdout, _ = process.communicate(input=input_data)
        
        if process.returncode == 0 and stdout.strip():
            selected_line = stdout.strip()
            parts = selected_line.split(' | ')
            if len(parts) >= 4:
                resource_name = parts[0]
                service_info = parts[1]
                url = parts[3]
                subprocess.run(['open', url], check=False)
                print(f"🚀 Opening {resource_name} ({service_info}) in AWS Console")
    except (OSError, subprocess.SubprocessError) as e:
        print(f"❌ Error in selection: {e}")

def show_settings_menu():
    """Show interactive settings menu"""
    while True:
        settings = load_settings()
        enabled_services = set(settings.get("enabled_services", SERVICE_CONFIG.keys()))
        
        print("\n🛠️  AWSF Settings")
        print("=" * 50)
        print()
        print("📋 Available Actions:")
        print("  1. 🔄 Repopulate resource list")
        print("  2. 🎛️  Toggle services")
        print("  3. 📊 View current settings")
        print("  4. ⚙️  Edit configuration")
        print("  5. 🔙 Back to search")
        print()
        
        choice = input("🔧 Select option (1-5): ").strip()
        
        if choice == "1":
            repopulate_resources()
        elif choice == "2":
            show_service_toggle_menu(enabled_services)
        elif choice == "3":
            show_current_settings(enabled_services)
        elif choice == "4":
            edit_configuration()
        elif choice == "5":
            break
        else:
            print("❌ Invalid option. Please select 1-5.")

def repopulate_resources():
    """Repopulate AWS resources"""
    print("\n🔄 Repopulating AWS resources...")
    scripts_dir = os.path.join(PROJECT_ROOT, "scripts")
    populate_script = os.path.join(scripts_dir, "populate_resources.py")
    
    try:
        result = subprocess.run(
            ["python3", populate_script],
            capture_output=True,
            text=True,
            cwd=scripts_dir,
            check=False
        )
        if result.returncode == 0:
            print("✅ Resource list updated successfully!")
        else:
            print(f"❌ Error updating resources: {result.stderr}")
    except (OSError, subprocess.SubprocessError) as e:
        print(f"❌ Error running populate script: {e}")
    input("\nPress Enter to continue...")

def show_service_toggle_menu(enabled_services):
    """Show service toggle menu"""
    while True:
        print("\n🎛️  Service Toggle Menu")
        print("=" * 30)
        
        for i, (service, config) in enumerate(SERVICE_CONFIG.items(), 1):
            status = "✅" if service in enabled_services else "❌"
            print(f"  {i}. {status} {config['icon']} {config['name']}")
        
        print(f"  {len(SERVICE_CONFIG)+1}. 🔄 Toggle all")
        print(f"  {len(SERVICE_CONFIG)+2}. 💾 Save & back")
        print()
        
        choice = input(f"🔧 Select service to toggle (1-{len(SERVICE_CONFIG)+2}): ").strip()
        
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(SERVICE_CONFIG):
                # Toggle individual service
                service = list(SERVICE_CONFIG.keys())[choice_num - 1]
                if service in enabled_services:
                    enabled_services.remove(service)
                    print(f"❌ Disabled {SERVICE_CONFIG[service]['name']}")
                else:
                    enabled_services.add(service)
                    print(f"✅ Enabled {SERVICE_CONFIG[service]['name']}")
                    
            elif choice_num == len(SERVICE_CONFIG) + 1:
                # Toggle all
                if len(enabled_services) == len(SERVICE_CONFIG):
                    enabled_services.clear()
                    print("❌ Disabled all services")
                else:
                    enabled_services.update(SERVICE_CONFIG.keys())
                    print("✅ Enabled all services")
                    
            elif choice_num == len(SERVICE_CONFIG) + 2:
                # Save and back
                if not enabled_services:
                    print("⚠️  Warning: No services enabled! Enabling all services.")
                    enabled_services.update(SERVICE_CONFIG.keys())
                
                settings = load_settings()
                settings["enabled_services"] = list(enabled_services)
                save_settings(settings)
                print("💾 Settings saved!")
                break
            else:
                print("❌ Invalid option.")
                
        except ValueError:
            print("❌ Please enter a valid number.")

def show_current_settings(enabled_services):
    """Show current settings"""
    config = load_config()
    
    print("\n📊 Current Settings:")
    print("=" * 30)
    print("🎛️  Enabled Services:")
    for service, service_config in SERVICE_CONFIG.items():
        status = "✅" if service in enabled_services else "❌"
        print(f"   {status} {service_config['icon']} {service_config['name']}")
    
    print("\n⚙️  Configuration:")
    print(f"   🌍 AWS Region: {config.get('aws_region', 'us-east-1')}")
    print(f"   👤 AWS Profile: {config.get('aws_profile', 'default')}")
    print(f"   🔗 Console URL: {config.get('console_base_url', 'https://console.aws.amazon.com')}")
    
    # Show resource count
    resources = load_aws_resources()
    if resources:
        enabled_count = sum(1 for r in resources.values() 
                          if r.get('service', '').lower() in enabled_services)
        total_count = len(resources)
        print(f"\n📈 Resources: {enabled_count}/{total_count} available")
    input("\nPress Enter to continue...")

def edit_configuration():
    """Edit configuration settings"""
    config = load_config()
    
    print("\n⚙️  Configuration Editor")
    print("=" * 30)
    print(f"Current AWS Region: {config.get('aws_region', 'us-east-1')}")
    new_region = input("Enter new AWS region (or press Enter to keep current): ").strip()
    if new_region:
        config['aws_region'] = new_region
    
    print(f"Current AWS Profile: {config.get('aws_profile', 'None')}")
    new_profile = input("Enter AWS profile (or press Enter for none): ").strip()
    if new_profile:
        config['aws_profile'] = new_profile
    elif new_profile == "":
        config['aws_profile'] = None
    
    save_config(config)
    print("✅ Configuration saved!")
    input("\nPress Enter to continue...")

def show_help():
    """Show help information"""
    print("🔍 AWSF - AWS Fuzzy Finder")
    print("=" * 50)
    print()
    print("A powerful fuzzy search tool for AWS resources across multiple services.")
    print()
    print("Usage:")
    print("  awsf                        # Interactive mode - all services")
    print("  awsf lambda payment         # Search Lambda functions for 'payment'")
    print("  awsf s3 media              # Search S3 buckets for 'media'")
    print("  awsf sqs queue             # Search SQS queues for 'queue'")
    print("  awsf payment               # Search all services for 'payment'")
    print("  awsf --settings            # Open settings menu (toggle services, repopulate resources, view stats)")
    print("  awsf --config              # Quick config edit (region, profile, console URL)")
    print()
    print("Supported Services:")
    for service, config in SERVICE_CONFIG.items():
        print(f"  {config['icon']} {service:<12} - {config['name']}")
    print()
    print("Examples:")
    print("  awsf lambda auth           # Find Lambda functions matching 'auth'")
    print("  awsf s3 media              # Find S3 buckets with 'media' in name")
    print("  awsf dynamodb user         # Find DynamoDB tables with 'user' in name")
    print("  awsf kinesis events        # Find Kinesis streams with 'events' in name")

def main():
    """Main entry point"""
    # Handle help
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        show_help()
        return
    
    # Handle settings
    if len(sys.argv) > 1 and sys.argv[1] in ['--settings', '-s', 'settings']:
        show_settings_menu()
        return
    
    # Handle quick config
    if len(sys.argv) > 1 and sys.argv[1] in ['--config', '-c', 'config']:
        edit_configuration()
        return
    
    # Parse arguments
    service_filter, search_query = parse_search_query(sys.argv[1:])
    
    # Check if service is enabled
    if service_filter:
        settings = load_settings()
        enabled_services = set(settings.get("enabled_services", SERVICE_CONFIG.keys()))
        if service_filter not in enabled_services:
            print(f"⚠️  Service '{service_filter}' is disabled in settings.")
            print("💡 Use '--settings' to enable services or search all enabled services.")
            return
    
    # Show header
    if service_filter:
        print(f"🔍 AWS {SERVICE_CONFIG[service_filter]['name']} Resource Search")
    else:
        print("🔍 AWSF - AWS Fuzzy Finder")
    print("=" * 50)
    
    # Show enabled services summary
    if not service_filter:
        settings = load_settings()
        enabled_services = settings.get("enabled_services", SERVICE_CONFIG.keys())
        disabled_count = len(SERVICE_CONFIG) - len(enabled_services)
        if disabled_count > 0:
            print(f"ℹ️  {len(enabled_services)}/{len(SERVICE_CONFIG)} services enabled. Use '--settings' to configure.")
        else:
            print(f"ℹ️  All {len(SERVICE_CONFIG)} services enabled.")
    
    if search_query:
        # Search with specific query
        search_with_query(search_query, service_filter)
    else:
        # Interactive mode
        try:
            # Check if fzf is available
            subprocess.run(['fzf', '--version'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL,
                         check=True)
            run_fzf_search(service_filter)
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("❌ fzf not found. Install with: brew install fzf")
            print("\nFalling back to simple search:")
            
            try:
                resources = load_aws_resources()
                if resources:
                    print("\n\n" + "─" * 60)
                    print("  📋 Manual Search Mode")
                    print("─" * 60)
                    query = input("\n\n    🔎 Enter search term: ").strip()
                    print("\n")
                    if query:
                        search_with_query(query, service_filter)
                else:
                    print("💡 Run: python3 scripts/populate_resources.py")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()