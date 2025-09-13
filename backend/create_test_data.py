#!/usr/bin/env python
"""
Script to create test data for the SainyaSecure military system
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'military_comm.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from army1.models import CommandMilitaryUser, Personnel, MilitaryMessage, Mission, CommandSecurityEvent

User = get_user_model()  # This will get the custom MilitaryUser model

def create_test_data():
    """Create comprehensive test data for all modules"""
    
    # Clean up existing test data
    print("🧹 Cleaning up existing test data...")
    User.objects.filter(username__in=['testcmd', 'testops', 'testintel']).delete()
    CommandMilitaryUser.objects.all().delete()
    Personnel.objects.all().delete()
    MilitaryMessage.objects.all().delete()
    Mission.objects.all().delete()
    CommandSecurityEvent.objects.filter(user__username__in=['testcmd', 'testops', 'testintel']).delete()

    try:
        # Create Django users first
        print("👤 Creating military users...")
        user1 = User.objects.create_user(
            username='testcmd', 
            password='testpass123', 
            email='cmd@military.base',
            military_id='CMD-001-2024',
            rank='Colonel',
            unit='HQ Command',
            branch='ARMY',
            clearance_level='TOP_SECRET',
            public_key='dummy_public_key_1',
            private_key_encrypted='dummy_encrypted_private_key_1'
        )
        
        user2 = User.objects.create_user(
            username='testops', 
            password='testpass123', 
            email='ops@military.base',
            military_id='OPS-002-2024',
            rank='Major',
            unit='Operations Division',
            branch='ARMY',
            clearance_level='SECRET',
            public_key='dummy_public_key_2',
            private_key_encrypted='dummy_encrypted_private_key_2'
        )
        
        user3 = User.objects.create_user(
            username='testintel', 
            password='testpass123', 
            email='intel@military.base',
            military_id='INT-003-2024',
            rank='Captain',
            unit='Intel Division',
            branch='INTELLIGENCE',
            clearance_level='TOP_SECRET',
            public_key='dummy_public_key_3',
            private_key_encrypted='dummy_encrypted_private_key_3'
        )
        
        # Create test military users (for army1 app)
        print("🪖 Creating command military users...")
        cmd_user = CommandMilitaryUser.objects.create(
            user=user1,
            military_id='CMD-001-2024',
            rank='COMMAND',
            branch='ARMY',
            clearance_level='TOP_SECRET',
            unit='HQ Command'
        )
        
        ops_user = CommandMilitaryUser.objects.create(
            user=user2,
            military_id='OPS-002-2024',
            rank='OPERATIONS',
            branch='ARMY',
            clearance_level='SECRET',
            unit='Operations Division'
        )
        
        intel_user = CommandMilitaryUser.objects.create(
            user=user3,
            military_id='INT-003-2024',
            rank='INTELLIGENCE',
            branch='INTELLIGENCE',
            clearance_level='TOP_SECRET',
            unit='Intel Division'
        )
        
        # Create test personnel
        print("👥 Creating personnel records...")
        personnel1 = Personnel.objects.create(
            military_user=cmd_user,
            first_name='John',
            last_name='Smith',
            service_number='CMD-001-2024',
            date_of_birth='1985-03-15',
            enlistment_date='2010-01-01',
            current_assignment='Command Operations',
            location='Base Alpha',
            emergency_contact_name='Jane Smith',
            emergency_contact_phone='+1-555-0001'
        )
        
        personnel2 = Personnel.objects.create(
            military_user=ops_user,
            first_name='Sarah',
            last_name='Johnson',
            service_number='OPS-002-2024',
            date_of_birth='1990-07-22',
            enlistment_date='2015-01-01',
            current_assignment='Field Operations',
            location='Base Bravo',
            emergency_contact_name='Mike Johnson',
            emergency_contact_phone='+1-555-0002'
        )
        
        personnel3 = Personnel.objects.create(
            military_user=intel_user,
            first_name='Alex',
            last_name='Rodriguez',
            service_number='INT-003-2024',
            date_of_birth='1988-12-10',
            enlistment_date='2012-01-01',
            current_assignment='Intelligence Analysis',
            location='Base Charlie',
            emergency_contact_name='Maria Rodriguez',
            emergency_contact_phone='+1-555-0003'
        )
        
        # Create test messages
        print("💬 Creating military messages...")
        msg1 = MilitaryMessage.objects.create(
            sender=user1,  # Use MilitaryUser instead of CommandMilitaryUser
            subject='Priority Alpha Protocol Activation',
            body='All units report status immediately. Priority Alpha protocol in effect.',
            priority='URGENT',
            classification='SECRET',
            status='SENT',
            requires_receipt=True
        )
        msg1.recipients.add(user2, user3)
        
        msg2 = MilitaryMessage.objects.create(
            sender=user2,
            subject='Operations Team Deployment Status',
            body='Operations team ready for deployment. All equipment checked and operational.',
            priority='NORMAL',
            classification='CONFIDENTIAL',
            status='SENT'
        )
        msg2.recipients.add(user1)
        
        msg3 = MilitaryMessage.objects.create(
            sender=user3,
            subject='Intelligence Briefing Schedule',
            body='Intelligence briefing scheduled for 0800 hours. Classified material distribution required.',
            priority='HIGH',
            classification='SECRET',
            status='SENT'
        )
        msg3.recipients.add(user1, user2)
        
        msg4 = MilitaryMessage.objects.create(
            sender=user1,
            subject='Mission Briefing Update',
            body='Mission briefing updated. Weather conditions favorable for air support.',
            priority='NORMAL',
            classification='UNCLASSIFIED',
            status='SENT'
        )
        msg4.recipients.add(user2, user3)
        
        # Create test missions
        print("🎯 Creating military missions...")
        mission1 = Mission.objects.create(
            mission_name='Operation Phoenix',
            mission_code='OP-PHX-001',
            description='Strategic reconnaissance and intelligence gathering mission in hostile territory.',
            classification='CONFIDENTIAL',
            commander=personnel1,
            status='PLANNING',
            start_date=timezone.now() + timedelta(days=3),
            location='Sector 7, Grid Reference Alpha-4-7',
            objectives='1. Gather intelligence on enemy positions\n2. Establish secure communication relay\n3. Extract high-value target if opportunity presents',
            resources_required='- 12 personnel (2 squads)\n- 2 armored vehicles\n- Communication equipment\n- Medical supplies'
        )
        
        mission2 = Mission.objects.create(
            mission_name='Operation Nightfall',
            mission_code='OP-NF-002',
            description='Night-time surveillance and patrol mission in border region.',
            classification='SECRET',
            commander=personnel2,
            status='IN_PROGRESS',
            start_date=timezone.now() - timedelta(hours=6),
            location='Border Sector 3',
            objectives='1. Monitor border activity\n2. Report suspicious movements\n3. Maintain radio silence unless emergency',
            resources_required='- 6 personnel (1 squad)\n- Night vision equipment\n- Communication gear'
        )
        
        mission3 = Mission.objects.create(
            mission_name='Operation Steel Shield',
            mission_code='OP-SS-003',
            description='Defensive perimeter establishment and fortification mission.',
            classification='UNCLASSIFIED',
            commander=personnel3,
            status='COMPLETED',
            start_date=timezone.now() - timedelta(days=5),
            end_date=timezone.now() - timedelta(days=1),
            location='Forward Operating Base Delta',
            objectives='1. Establish defensive positions\n2. Install surveillance equipment\n3. Train local security forces',
            resources_required='- 24 personnel (4 squads)\n- Construction equipment\n- Security systems'
        )
        
        # Create some security events
        print("🔒 Creating security events...")
        CommandSecurityEvent.objects.create(
            user=user1,
            event_type='LOGIN_SUCCESS',
            severity='LOW',
            description='Successful login from command terminal',
            ip_address='192.168.1.100',
            module_accessed='Dashboard'
        )
        
        CommandSecurityEvent.objects.create(
            user=user2,
            event_type='ACCESS_GRANTED',
            severity='MEDIUM',
            description='Access granted to Operations module',
            ip_address='192.168.1.101',
            module_accessed='Operations'
        )
        
        CommandSecurityEvent.objects.create(
            user=user3,
            event_type='SECURITY_VIOLATION',
            severity='HIGH',
            description='Attempted access to restricted intelligence files',
            ip_address='192.168.1.102',
            module_accessed='Intelligence'
        )
        
        CommandSecurityEvent.objects.create(
            user=user1,
            event_type='2FA_SUCCESS',
            severity='LOW',
            description='Two-factor authentication completed successfully',
            ip_address='192.168.1.100',
            module_accessed='Login'
        )
        
        CommandSecurityEvent.objects.create(
            user=user2,
            event_type='ACCESS_DENIED',
            severity='MEDIUM',
            description='Access denied to classified mission files',
            ip_address='192.168.1.101',
            module_accessed='Mission Control'
        )
        
        # Print summary
        print("\n✅ Test data created successfully!")
        print("=" * 50)
        print(f"👤 Users created: {User.objects.filter(username__in=['testcmd', 'testops', 'testintel']).count()}")
        print(f"🪖 Military Users created: {CommandMilitaryUser.objects.count()}")
        print(f"👥 Personnel created: {Personnel.objects.count()}")
        print(f"💬 Messages created: {MilitaryMessage.objects.count()}")
        print(f"🎯 Missions created: {Mission.objects.count()}")
        print(f"🔒 Security Events created: {CommandSecurityEvent.objects.count()}")
        print("=" * 50)
        
        # Show some sample data
        print("\n📊 Sample Data Overview:")
        print("\nPersonnel:")
        for p in Personnel.objects.all():
            print(f"  - {p.first_name} {p.last_name} ({p.military_user.rank}) - {p.current_assignment}")
        
        print("\nMissions:")
        for m in Mission.objects.all():
            print(f"  - {m.mission_name} ({m.mission_code}) - Status: {m.status}")
        
        print(f"\nMessages: {MilitaryMessage.objects.count()} messages across different channels")
        print(f"Security Events: {CommandSecurityEvent.objects.count()} events logged")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🚀 Starting test data creation for SainyaSecure...")
    success = create_test_data()
    
    if success:
        print("\n🎉 Test data creation completed successfully!")
        print("You can now test the modules with real data.")
    else:
        print("\n💥 Test data creation failed!")
        sys.exit(1)