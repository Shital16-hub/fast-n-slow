#!/usr/bin/env python3
# fusionpbx_livekit_helper.py
# Helper script to generate FusionPBX configuration for LiveKit Cloud integration

import os
import json
import sys
from dotenv import load_dotenv

def load_environment():
    """Load environment variables"""
    load_dotenv()
    
    required_vars = [
        'LIVEKIT_SIP_URI',
        'PRIMARY_PHONE_NUMBER',
        'FREESWITCH_SERVER_IP'
    ]
    
    config = {}
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value or (var == 'LIVEKIT_SIP_URI' and value.startswith('sip:YOUR_')):
            missing_vars.append(var)
        else:
            config[var] = value
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please update your .env file with the correct values.")
        sys.exit(1)
    
    return config

def extract_sip_domain(sip_uri):
    """Extract domain from SIP URI"""
    # sip:abc123.sip.livekit.cloud → abc123.sip.livekit.cloud
    return sip_uri.replace('sip:', '')

def print_fusionpbx_configuration(config):
    """Print complete FusionPBX configuration guide"""
    
    sip_domain = extract_sip_domain(config['LIVEKIT_SIP_URI'])
    phone_number = config['PRIMARY_PHONE_NUMBER']
    freeswitch_ip = config['FREESWITCH_SERVER_IP']
    
    print("🔧 FUSIONPBX CONFIGURATION FOR LIVEKIT CLOUD")
    print("=" * 60)
    print(f"LiveKit SIP Domain: {sip_domain}")
    print(f"Phone Number: {phone_number}")
    print(f"FreeSwitch Server: {freeswitch_ip}")
    print()
    
    # Step 1: Gateway Configuration
    print("STEP 1: CREATE GATEWAY")
    print("-" * 30)
    print("Navigate to: Accounts → Gateways → Add Gateway")
    print()
    print("Fill in these fields:")
    print(f"  Gateway Name: livekit-cloud-gateway")
    print(f"  Username: (leave empty)")
    print(f"  Password: (leave empty)")
    print(f"  Proxy: {sip_domain}:5060")
    print(f"  Register: false")
    print(f"  Context: public")
    print(f"  Profile: external")
    print(f"  Enabled: true")
    print(f"  Description: LiveKit Cloud SIP Gateway for Voice AI")
    print()
    print("Click 'Save' to create the gateway.")
    print()
    
    # Step 2: Ring Group Configuration
    print("STEP 2: CREATE RING GROUP")
    print("-" * 30)
    print("Navigate to: Apps → Ring Groups → Add")
    print()
    print("Fill in these fields:")
    print(f"  Name: livekit-voice-ai")
    print(f"  Extension: 8888")
    print(f"  Strategy: simultaneous")
    print(f"  Ring Back: us-ring")
    print(f"  Context: default")
    print(f"  Enabled: true")
    print(f"  Description: LiveKit Voice AI Ring Group")
    print()
    print("In the Destinations section, click '+' and add:")
    print(f"  Destination: sofia/gateway/livekit-cloud-gateway/{phone_number}@{sip_domain}")
    print(f"  Timeout: 30")
    print(f"  Delay: 0")
    print()
    print("Click 'Save' to create the ring group.")
    print()
    
    # Step 3: Inbound Route Configuration
    print("STEP 3: CONFIGURE INBOUND ROUTE")
    print("-" * 35)
    print("Navigate to: Dialplan → Destinations")
    print()
    print("Find or create your inbound route:")
    print(f"  Destination Number: {phone_number}")
    print(f"  Caller ID Number: {phone_number}")
    print(f"  Context: public")
    print(f"  Domain Name: default")
    print(f"  Enabled: true")
    print(f"  Description: Inbound route for {phone_number} to LiveKit Voice AI")
    print()
    print("In the Actions section:")
    print(f"  Action: transfer")
    print(f"  Data: 8888 XML default")
    print(f"  Inline: false")
    print()
    print("Click 'Save' to update the inbound route.")
    print()
    
    # Step 4: Verification
    print("STEP 4: VERIFICATION")
    print("-" * 20)
    print("After saving all configurations:")
    print()
    print("1. Restart FreeSwitch profiles:")
    print("   fs_cli -x 'sofia profile external restart'")
    print()
    print("2. Check gateway status:")
    print("   fs_cli -x 'sofia profile external gwlist'")
    print("   (Should show 'livekit-cloud-gateway' as UP)")
    print()
    print("3. Test connectivity:")
    print(f"   fs_cli -x 'originate sofia/gateway/livekit-cloud-gateway/test@{sip_domain} &echo'")
    print()

def generate_json_configs(config):
    """Generate JSON configuration files"""
    
    sip_domain = extract_sip_domain(config['LIVEKIT_SIP_URI'])
    phone_number = config['PRIMARY_PHONE_NUMBER']
    
    configs = {
        "gateway": {
            "gateway_name": "livekit-cloud-gateway",
            "proxy": f"{sip_domain}:5060",
            "register": False,
            "context": "public",
            "profile": "external",
            "enabled": True,
            "description": "LiveKit Cloud SIP Gateway for Voice AI"
        },
        "ringgroup": {
            "name": "livekit-voice-ai",
            "extension": "8888",
            "strategy": "simultaneous",
            "destinations": [
                f"sofia/gateway/livekit-cloud-gateway/{phone_number}@{sip_domain}"
            ],
            "description": "LiveKit Voice AI Ring Group"
        },
        "inbound_route": {
            "destination_number": phone_number,
            "caller_id_number": phone_number,
            "actions": [
                {
                    "action": "transfer",
                    "data": "8888 XML default"
                }
            ]
        }
    }
    
    # Export configurations
    for config_type, config_data in configs.items():
        filename = f"fusionpbx_{config_type}_livekit.json"
        with open(filename, 'w') as f:
            json.dump(config_data, f, indent=2)
        print(f"✅ Exported: {filename}")

def generate_test_commands(config):
    """Generate test commands"""
    
    sip_domain = extract_sip_domain(config['LIVEKIT_SIP_URI'])
    phone_number = config['PRIMARY_PHONE_NUMBER']
    freeswitch_ip = config['FREESWITCH_SERVER_IP']
    
    print("\n🧪 TESTING COMMANDS")
    print("=" * 30)
    print()
    
    print("Network Connectivity Tests:")
    print(f"  nslookup {sip_domain}")
    print(f"  ping {sip_domain}")
    print(f"  telnet {sip_domain} 5060")
    print()
    
    print("FreeSwitch Tests (run in fs_cli):")
    print(f"  sofia profile external gwlist")
    print(f"  sofia status gateway livekit-cloud-gateway")
    print(f"  originate sofia/gateway/livekit-cloud-gateway/test@{sip_domain} &echo")
    print()
    
    print("Full Call Test:")
    print(f"  1. Start your Voice AI: python main.py dev")
    print(f"  2. Call {phone_number}")
    print(f"  3. Should hear: 'Roadside assistance, this is Mark, how can I help you today?'")
    print()

def main():
    """Main function"""
    print("🔧 FUSIONPBX + LIVEKIT CLOUD CONFIGURATION HELPER")
    print("=" * 60)
    
    # Load configuration
    try:
        config = load_environment()
    except SystemExit:
        return
    
    print("📋 Configuration loaded successfully:")
    print(f"   LiveKit SIP URI: {config['LIVEKIT_SIP_URI']}")
    print(f"   Phone Number: {config['PRIMARY_PHONE_NUMBER']}")
    print(f"   FreeSwitch IP: {config['FREESWITCH_SERVER_IP']}")
    print()
    
    # Print configuration guide
    print_fusionpbx_configuration(config)
    
    # Generate JSON configs
    print("📄 EXPORTING CONFIGURATION FILES")
    print("=" * 40)
    generate_json_configs(config)
    print()
    
    # Generate test commands
    generate_test_commands(config)
    
    print("🎉 Configuration helper completed!")
    print("   Use the guide above to configure FusionPBX manually.")
    print("   Reference the exported JSON files for automation.")

if __name__ == "__main__":
    main()