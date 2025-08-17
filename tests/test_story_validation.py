#!/usr/bin/env python3
"""
Test Story Validation
Debug the story validation to understand why personalness scores are low
"""

import requests
import json

def test_story_validation():
    """Test story validation with different stories"""
    
    stories = [
        {
            "name": "Story 1 (Original)",
            "story": "When I was 12, I secretly built my first computer from spare parts in my dad's garage workshop behind the old tool cabinet, and I cried happy tears when it actually booted up and played my favorite game because I felt like a genius and my dad was so proud of me"
        },
        {
            "name": "Story 2 (Grandmother)",
            "story": "My grandmother secretly taught me to bake her famous chocolate chip cookies every Sunday afternoon in her kitchen with the yellow wallpaper, and I still remember the smell of vanilla and butter and how she would always let me lick the spoon first because I was her favorite grandchild and she said I had the magic touch that made them taste better than anyone else's"
        },
        {
            "name": "Story 3 (Simple Personal)",
            "story": "When I was 8, my first pet was a goldfish named Bubbles that I secretly won at the county fair, and I cried for days when it died because I felt like I had failed to take care of my very first responsibility"
        },
        {
            "name": "Story 4 (Very Personal)",
            "story": "My older sister Sarah and I discovered a hidden compartment behind the loose brick in our basement wall when I was 9, and we secretly stashed our Halloween candy there every October because we were terrified our parents would find our sugar hoard, but I felt like we were pirates with buried treasure"
        }
    ]
    
    print("🔍 Testing Story Validation")
    print("=" * 50)
    
    for i, story_data in enumerate(stories, 1):
        print(f"\n📖 Test {i}: {story_data['name']}")
        print("-" * 30)
        print(f"Story: {story_data['story'][:100]}...")
        
        try:
            response = requests.post(
                'http://localhost:5000/api/memoryvault/validate-story',
                json={'story': story_data['story']},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result['status'] == 'success':
                    data = result['data']
                    print(f"✅ Score: {data['personalness_score']:.2f}")
                    print(f"   Elements: {data['personal_elements_count']}")
                    print(f"   Types: {data['element_types']}")
                    print(f"   Keywords: {data.get('personal_keywords_found', 'N/A')}")
                    if data.get('recommendations'):
                        print(f"   Recommendations: {data['recommendations'][:2]}...")
                else:
                    print(f"❌ Validation failed: {result['message']}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_story_validation() 