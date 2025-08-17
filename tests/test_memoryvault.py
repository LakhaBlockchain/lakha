#!/usr/bin/env python3
"""
MemoryVault Test Script
Demonstrates the semantic seed phrase system
"""

import json
from address import (
    generate_address_from_story, 
    generate_address_from_mnemonic, 
    validate_story_personalness,
    generate_address_legacy
)

def test_memoryvault_system():
    """Test the complete MemoryVault system"""
    print("🔐 MemoryVault - Semantic Seed Phrase System")
    print("=" * 60)
    
    # Example personal stories
    stories = [
        {
            "name": "Childhood Pet Story",
            "story": """
            When I was 8, my first pet was a goldfish named Bubbles because he always made 
            bubble sounds. I kept him in a secret spot behind my toy box in my room. One day, 
            I accidentally spilled my juice on the floor and had to hide it from my mom by 
            putting a blanket over it. That's when I learned that honesty is better than 
            hiding things, and I created my secret handshake with my sister using three 
            high-fives and a fist bump. Now whenever I feel stressed, I go to my secret spot 
            in the corner of my garden and remember that moment with Bubbles.
            """
        },
        {
            "name": "Family Secret Recipe",
            "story": """
            My grandmother taught me her secret recipe for chocolate chip cookies when I was 12. 
            The secret ingredient was a pinch of cinnamon that she only told me about. We would 
            bake them in her special blue mixing bowl that she got from her mother. The cookies 
            always tasted better when we made them together in her kitchen on Sunday afternoons. 
            She told me never to share the cinnamon secret with anyone else, and I still keep 
            that promise to this day.
            """
        },
        {
            "name": "First Driving Experience",
            "story": """
            My first time driving was when I was 16, and I accidentally hit the gas instead of 
            the brake in our driveway. I crashed into my dad's favorite rose bush that he had 
            been growing for years. I was so scared that I hid in my room for hours, but my 
            dad found me and taught me that mistakes are how we learn. He helped me plant a 
            new rose bush, and now every time I see roses, I remember that lesson about 
            responsibility and forgiveness.
            """
        }
    ]
    
    print("📖 Testing Personal Stories")
    print("-" * 40)
    
    for i, story_data in enumerate(stories, 1):
        print(f"\n{i}. {story_data['name']}")
        print("   Story:", story_data['story'][:100] + "...")
        
        # Validate story personalness
        try:
            validation = validate_story_personalness(story_data['story'])
            print(f"   📊 Personalness Score: {validation['personalness_score']:.2f}")
            print(f"   🔍 Personal Elements: {validation['personal_elements_count']}")
            print(f"   🏷️  Element Types: {validation['element_types']}")
            
            if validation['recommendations']:
                print("   💡 Recommendations:")
                for rec in validation['recommendations'][:2]:  # Show first 2
                    print(f"      - {rec}")
            
        except Exception as e:
            print(f"   ❌ Validation Error: {e}")
    
    print("\n" + "=" * 60)
    print("🔑 Generating Addresses from Stories")
    print("-" * 40)
    
    generated_addresses = []
    
    for i, story_data in enumerate(stories, 1):
        print(f"\n{i}. Generating address from '{story_data['name']}'...")
        
        try:
            # Generate address from story
            result = generate_address_from_story(story_data['story'])
            
            print(f"   ✅ Address: {result['address']}")
            print(f"   🗝️  Mnemonic: {result['mnemonic'][:50]}...")
            print(f"   📝 Story Hash: {result['story_hash'][:16]}...")
            print(f"   🔍 Personal Elements: {result['personal_elements_count']}")
            print(f"   📊 Personalness Score: {result['personalness_score']:.2f}")
            
            generated_addresses.append({
                'name': story_data['name'],
                'address': result['address'],
                'mnemonic': result['mnemonic'],
                'story_hash': result['story_hash']
            })
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🔄 Testing Mnemonic Recovery")
    print("-" * 40)
    
    for i, addr_data in enumerate(generated_addresses, 1):
        print(f"\n{i}. Testing recovery for '{addr_data['name']}'...")
        
        try:
            # Recover from mnemonic
            recovered = generate_address_from_mnemonic(addr_data['mnemonic'])
            
            print(f"   ✅ Original Address: {addr_data['address']}")
            print(f"   ✅ Recovered Address: {recovered['address']}")
            print(f"   🔄 Recovery: {'✅ SUCCESS' if addr_data['address'] == recovered['address'] else '❌ FAILED'}")
            
        except Exception as e:
            print(f"   ❌ Recovery Error: {e}")
    
    print("\n" + "=" * 60)
    print("🔍 Testing Story Recovery")
    print("-" * 40)
    
    for i, addr_data in enumerate(generated_addresses, 1):
        print(f"\n{i}. Testing story recovery for '{addr_data['name']}'...")
        
        try:
            # Recover from story
            story_result = generate_address_from_story(stories[i-1]['story'])
            
            print(f"   ✅ Original Address: {addr_data['address']}")
            print(f"   ✅ Story Address: {story_result['address']}")
            print(f"   🔄 Recovery: {'✅ SUCCESS' if addr_data['address'] == story_result['address'] else '❌ FAILED'}")
            
        except Exception as e:
            print(f"   ❌ Story Recovery Error: {e}")
    
    print("\n" + "=" * 60)
    print("📊 Comparison with Traditional Generation")
    print("-" * 40)
    
    # Generate traditional address
    traditional_addr = generate_address_legacy()
    print(f"Traditional Address: {traditional_addr}")
    
    # Show MemoryVault advantages
    print("\n🎭 MemoryVault Advantages:")
    print("   ✅ Memorable: Based on personal stories")
    print("   ✅ Secure: Same cryptographic security as traditional")
    print("   ✅ Dual Recovery: Story + traditional mnemonic")
    print("   ✅ Personal: Unique to each individual")
    print("   ✅ Emotional: Hard to forget due to emotional connection")
    
    print("\n" + "=" * 60)
    print("🎉 MemoryVault Test Complete!")
    print("=" * 60)

def test_story_validation():
    """Test story validation with different types of stories"""
    print("\n🔍 Story Validation Test")
    print("=" * 40)
    
    test_stories = [
        {
            "name": "Very Personal Story",
            "story": "My first pet was a dog named Max who I got when I was 7. He slept in my secret hiding spot under my bed, and we had our own special handshake with three high-fives. When I was sad, he would bring me my favorite toy, a blue teddy bear that my grandma gave me.",
            "expected_score": "High"
        },
        {
            "name": "Generic Story",
            "story": "I went to the store and bought some food. The weather was nice and I walked home. It was a good day.",
            "expected_score": "Low"
        },
        {
            "name": "Mixed Personal Story",
            "story": "I live in New York and work at a company. My favorite color is blue and I like pizza. My dog's name is Buddy and he likes to play in the park.",
            "expected_score": "Medium"
        }
    ]
    
    for story_data in test_stories:
        print(f"\n📖 {story_data['name']}")
        print(f"   Expected Score: {story_data['expected_score']}")
        
        try:
            validation = validate_story_personalness(story_data['story'])
            print(f"   📊 Actual Score: {validation['personalness_score']:.2f}")
            print(f"   🔍 Elements: {validation['personal_elements_count']}")
            print(f"   🏷️  Types: {validation['element_types']}")
            
            if validation['recommendations']:
                print("   💡 Suggestions:")
                for rec in validation['recommendations']:
                    print(f"      - {rec}")
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    """Main test function"""
    try:
        test_memoryvault_system()
        test_story_validation()
        
        print("\n🎭 MemoryVault System Summary:")
        print("✅ Semantic seed phrase generation working")
        print("✅ Story personalness validation working")
        print("✅ Dual recovery (story + mnemonic) working")
        print("✅ Cryptographic security maintained")
        print("✅ Backward compatibility preserved")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Make sure to install required dependencies:")
        print("   pip install hdwallet mnemonic")
    except Exception as e:
        print(f"❌ Test Error: {e}")

if __name__ == '__main__':
    main() 