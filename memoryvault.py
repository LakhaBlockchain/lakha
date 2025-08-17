#!/usr/bin/env python3
"""
MemoryVault - Semantic Seed Phrase System
Transforms personal memories into cryptographic keys
"""

import hashlib
import hmac
import secrets
import re
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import bech32
import hdwallet
from hdwallet import HDWallet
from hdwallet.cryptocurrencies import Bitcoin
from hdwallet.derivations import BIP44Derivation
import mnemonic

@dataclass
class StoryElement:
    """Represents a personal story element"""
    element_type: str  # 'name', 'location', 'date', 'emotion', 'action', 'object'
    value: str
    confidence: float  # How confident we are this is a personal element (0.0-1.0)
    position: int  # Position in the story
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'element_type': self.element_type,
            'value': self.value,
            'confidence': self.confidence,
            'position': self.position
        }

@dataclass
class MemoryVaultSeed:
    """Represents a MemoryVault seed"""
    story_hash: str
    personal_elements: List[StoryElement]
    normalized_story: str
    entropy: bytes
    mnemonic: str
    private_key: str
    public_key: str
    address: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'story_hash': self.story_hash,
            'personal_elements': [elem.to_dict() for elem in self.personal_elements],
            'normalized_story': self.normalized_story,
            'entropy': self.entropy.hex() if isinstance(self.entropy, bytes) else str(self.entropy),
            'mnemonic': self.mnemonic,
            'private_key': self.private_key,
            'public_key': self.public_key,
            'address': self.address
        }

class MemoryVault:
    """MemoryVault - Semantic Seed Phrase System"""
    
    def __init__(self):
        # Personal element patterns for extraction
        self.personal_patterns = {
            'name': [
                r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Names with capitals
                r'\b(?:my|our)\s+([a-z]+)\b',  # "my dog", "our cat"
                r'\b(?:named|called)\s+([a-z]+)\b',  # "named Fluffy"
            ],
            'location': [
                r'\b(?:in|at|behind|under|near)\s+([a-z\s]+)\b',  # Locations
                r'\b(?:room|house|garden|park|school|work)\b',  # Common places
            ],
            'date': [
                r'\b(?:when|on|during)\s+(?:I was|I was|we were)\s+(\d+)\b',  # Ages
                r'\b(?:first|last|next|previous)\s+(?:time|day|week|month|year)\b',
            ],
            'emotion': [
                r'\b(?:felt|was|were)\s+(?:happy|sad|scared|excited|proud|embarrassed|nervous|confident)\b',
                r'\b(?:made me|made us)\s+(?:feel|realize|understand)\b',
            ],
            'action': [
                r'\b(?:I|we)\s+(?:went|did|made|created|found|discovered|learned|taught)\b',
                r'\b(?:secret|hidden|private|special)\s+([a-z\s]+)\b',
            ],
            'object': [
                r'\b(?:my|our)\s+([a-z]+)\b',  # Personal objects
                r'\b(?:first|favorite|special)\s+([a-z]+)\b',  # Important objects
            ]
        }
        
        # Personal keywords that indicate private information
        self.personal_keywords = {
            'family': ['mom', 'dad', 'sister', 'brother', 'grandma', 'grandpa', 'aunt', 'uncle'],
            'pets': ['dog', 'cat', 'fish', 'bird', 'hamster', 'rabbit'],
            'emotions': ['happy', 'sad', 'scared', 'excited', 'proud', 'embarrassed', 'nervous'],
            'secrets': ['secret', 'hidden', 'private', 'special', 'only', 'never told'],
            'firsts': ['first time', 'first pet', 'first crush', 'first car', 'first job'],
            'personal': ['my', 'our', 'mine', 'ours', 'personal', 'private']
        }
    
    def extract_personal_elements(self, story: str) -> List[StoryElement]:
        """Extract personal elements from a story"""
        elements = []
        story_lower = story.lower()
        
        # Extract names
        for pattern in self.personal_patterns['name']:
            matches = re.finditer(pattern, story, re.IGNORECASE)
            for match in matches:
                name = match.group(1) if match.groups() else match.group(0)
                if self._is_personal_name(name):
                    elements.append(StoryElement(
                        element_type='name',
                        value=name.strip(),
                        confidence=self._calculate_confidence(name, 'name'),
                        position=match.start()
                    ))
        
        # Extract locations
        for pattern in self.personal_patterns['location']:
            matches = re.finditer(pattern, story, re.IGNORECASE)
            for match in matches:
                location = match.group(1) if match.groups() else match.group(0)
                if self._is_personal_location(location):
                    elements.append(StoryElement(
                        element_type='location',
                        value=location.strip(),
                        confidence=self._calculate_confidence(location, 'location'),
                        position=match.start()
                    ))
        
        # Extract emotions
        for pattern in self.personal_patterns['emotion']:
            matches = re.finditer(pattern, story, re.IGNORECASE)
            for match in matches:
                emotion = match.group(0)
                elements.append(StoryElement(
                    element_type='emotion',
                    value=emotion.strip(),
                    confidence=0.8,  # Emotions are usually personal
                    position=match.start()
                ))
        
        # Extract actions
        for pattern in self.personal_patterns['action']:
            matches = re.finditer(pattern, story, re.IGNORECASE)
            for match in matches:
                action = match.group(0)
                if self._is_personal_action(action):
                    elements.append(StoryElement(
                        element_type='action',
                        value=action.strip(),
                        confidence=self._calculate_confidence(action, 'action'),
                        position=match.start()
                    ))
        
        # Extract objects
        for pattern in self.personal_patterns['object']:
            matches = re.finditer(pattern, story, re.IGNORECASE)
            for match in matches:
                obj = match.group(1) if match.groups() else match.group(0)
                if self._is_personal_object(obj):
                    elements.append(StoryElement(
                        element_type='object',
                        value=obj.strip(),
                        confidence=self._calculate_confidence(obj, 'object'),
                        position=match.start()
                    ))
        
        # Sort by position and remove duplicates
        elements.sort(key=lambda x: x.position)
        unique_elements = []
        seen_values = set()
        
        for element in elements:
            if element.value.lower() not in seen_values:
                unique_elements.append(element)
                seen_values.add(element.value.lower())
        
        return unique_elements
    
    def _is_personal_name(self, name: str) -> bool:
        """Check if a name is likely personal"""
        name_lower = name.lower()
        
        # Skip common words that aren't names
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        if name_lower in common_words:
            return False
        
        # Check if it contains personal keywords
        for keyword_list in self.personal_keywords.values():
            if any(keyword in name_lower for keyword in keyword_list):
                return True
        
        # Check if it's capitalized (likely a name)
        if name[0].isupper() and len(name) > 2:
            return True
        
        return False
    
    def _is_personal_location(self, location: str) -> bool:
        """Check if a location is likely personal"""
        location_lower = location.lower()
        
        # Check for personal location keywords
        personal_locations = ['room', 'house', 'garden', 'backyard', 'basement', 'attic', 'closet']
        if any(loc in location_lower for loc in personal_locations):
            return True
        
        # Check for possessive pronouns
        if any(pronoun in location_lower for pronoun in ['my', 'our', 'mine', 'ours']):
            return True
        
        return False
    
    def _is_personal_action(self, action: str) -> bool:
        """Check if an action is likely personal"""
        action_lower = action.lower()
        
        # Check for personal action keywords
        personal_actions = ['secret', 'hidden', 'private', 'special', 'first', 'only']
        if any(keyword in action_lower for keyword in personal_actions):
            return True
        
        return False
    
    def _is_personal_object(self, obj: str) -> bool:
        """Check if an object is likely personal"""
        obj_lower = obj.lower()
        
        # Check for personal object keywords
        personal_objects = ['pet', 'toy', 'book', 'gift', 'treasure', 'collection']
        if any(keyword in obj_lower for keyword in personal_objects):
            return True
        
        return False
    
    def _calculate_confidence(self, value: str, element_type: str) -> float:
        """Calculate confidence that an element is personal"""
        value_lower = value.lower()
        confidence = 0.5  # Base confidence
        
        # Boost confidence for personal keywords
        for keyword_list in self.personal_keywords.values():
            if any(keyword in value_lower for keyword in keyword_list):
                confidence += 0.2
        
        # Boost for specific element types
        if element_type == 'name' and value[0].isupper():
            confidence += 0.2
        elif element_type == 'location' and any(loc in value_lower for loc in ['room', 'house', 'garden']):
            confidence += 0.2
        elif element_type == 'action' and any(action in value_lower for action in ['secret', 'hidden', 'private']):
            confidence += 0.3
        
        return min(1.0, confidence)
    
    def normalize_story(self, story: str) -> str:
        """Normalize the story for consistent processing with flexible matching"""
        # Convert to lowercase
        normalized = story.lower()
        
        # Remove extra whitespace and normalize
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove punctuation except for important separators
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Normalize common variations and synonyms
        replacements = {
            # Time variations
            'first time': 'firsttime', 'first': 'first', '1st': 'first',
            'second time': 'secondtime', 'second': 'second', '2nd': 'second',
            'third time': 'thirdtime', 'third': 'third', '3rd': 'third',
            
            # Location variations
            'secret spot': 'secretspot', 'secret place': 'secretspot', 'hiding place': 'secretspot',
            'hideout': 'secretspot', 'secret hideout': 'secretspot',
            'backyard': 'backyard', 'garden': 'garden', 'yard': 'garden',
            'room': 'room', 'bedroom': 'room', 'living room': 'room',
            'house': 'house', 'home': 'house', 'apartment': 'house',
            
            # Family variations
            'grandmother': 'grandma', 'grandma': 'grandma', 'granny': 'grandma',
            'grandfather': 'grandpa', 'grandpa': 'grandpa', 'granddad': 'grandpa',
            'mother': 'mom', 'mom': 'mom', 'mum': 'mom', 'mama': 'mom',
            'father': 'dad', 'dad': 'dad', 'daddy': 'dad', 'papa': 'dad',
            'sister': 'sister', 'sis': 'sister', 'little sister': 'sister',
            'brother': 'brother', 'bro': 'brother', 'little brother': 'brother',
            
            # Pet variations
            'pet': 'pet', 'animal': 'pet', 'dog': 'dog', 'puppy': 'dog',
            'cat': 'cat', 'kitten': 'cat', 'fish': 'fish', 'goldfish': 'fish',
            
            # Emotion variations
            'happy': 'happy', 'excited': 'happy', 'joyful': 'happy',
            'sad': 'sad', 'upset': 'sad', 'disappointed': 'sad',
            'scared': 'scared', 'afraid': 'scared', 'frightened': 'scared',
            'proud': 'proud', 'proud of': 'proud',
            
            # Action variations
            'learned': 'learned', 'discovered': 'learned', 'found out': 'learned',
            'created': 'created', 'made': 'created', 'built': 'created',
            'hid': 'hid', 'hidden': 'hid', 'buried': 'hid',
            
            # Object variations
            'diary': 'diary', 'journal': 'diary', 'notebook': 'diary',
            'toy': 'toy', 'toy box': 'toy', 'toybox': 'toy',
            'vase': 'vase', 'ceramic vase': 'vase',
            'piano': 'piano', 'old piano': 'piano', 'wooden piano': 'piano',
            
            # Personal keywords
            'my': 'my', 'mine': 'my', 'our': 'our', 'ours': 'our',
            'secret': 'secret', 'private': 'secret', 'personal': 'secret',
            'family': 'family', 'home': 'family',
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        # Sort words to make order less important
        words = normalized.split()
        # Keep important words in order but normalize common variations
        important_words = []
        for word in words:
            if len(word) > 3:  # Keep longer words as important
                important_words.append(word)
        
        # Create a more flexible hash by focusing on key elements
        return ' '.join(important_words).strip()
    
    def create_story_hash(self, story: str, elements: List[StoryElement]) -> str:
        """Create a hash from the story and personal elements"""
        # Normalize the story
        normalized_story = self.normalize_story(story)
        
        # Create element hashes
        element_hashes = []
        for element in elements:
            element_data = f"{element.element_type}:{element.value}:{element.confidence}"
            element_hash = hashlib.sha256(element_data.encode()).hexdigest()
            element_hashes.append(element_hash)
        
        # Combine story and element hashes
        combined_data = normalized_story + "".join(element_hashes)
        
        # Create final hash
        story_hash = hashlib.sha256(combined_data.encode()).hexdigest()
        
        return story_hash
    
    def generate_entropy_from_story(self, story_hash: str) -> bytes:
        """Generate entropy from story hash"""
        # Use HMAC with a fixed key for deterministic generation
        key = b"MemoryVault_Entropy_Key_v1"
        entropy = hmac.new(key, story_hash.encode(), hashlib.sha256).digest()
        
        # Ensure we have enough entropy (32 bytes for BIP39)
        if len(entropy) < 32:
            # Extend entropy if needed
            extended_entropy = entropy
            while len(extended_entropy) < 32:
                extended_entropy += hashlib.sha256(entropy + extended_entropy).digest()
            entropy = extended_entropy[:32]
        
        return entropy
    
    def generate_mnemonic_from_entropy(self, entropy: bytes) -> str:
        """Generate BIP39 mnemonic from entropy"""
        # Convert entropy to mnemonic
        mnemonic_words = mnemonic.Mnemonic('english').to_mnemonic(entropy)
        return mnemonic_words
    
    def generate_keypair_from_mnemonic(self, mnemonic: str) -> Tuple[str, str, str]:
        """Generate keypair from mnemonic"""
        try:
            # Initialize HD wallet
            hdwallet = HDWallet(cryptocurrency=Bitcoin)
            
            # Set mnemonic
            hdwallet.mnemonic = mnemonic
            
            # Derive BIP44 path for Bitcoin
            hdwallet.from_path("m/44'/0'/0'/0/0")
            
            # Get private and public keys
            private_key = hdwallet.private_key()
            public_key = hdwallet.public_key()
            
            # Generate Bech32 address
            address = hdwallet.address()
            
            return private_key, public_key, address
        except Exception as e:
            # Fallback: generate simple address from mnemonic hash
            mnemonic_hash = hashlib.sha256(mnemonic.encode()).digest()
            private_key = mnemonic_hash.hex()
            public_key = hashlib.sha256(mnemonic_hash).hexdigest()
            
            # Generate Lakha address
            from address import encode_address
            address = encode_address(mnemonic_hash[:20])  # Use first 20 bytes
            
            return private_key, public_key, address
    
    def create_memory_vault_seed(self, story: str) -> MemoryVaultSeed:
        """Create a MemoryVault seed from a personal story"""
        # Extract personal elements
        elements = self.extract_personal_elements(story)
        
        if not elements:
            raise ValueError("No personal elements found in story. Please include more personal details.")
        
        # Create story hash
        story_hash = self.create_story_hash(story, elements)
        
        # Generate entropy
        entropy = self.generate_entropy_from_story(story_hash)
        
        # Generate mnemonic
        mnemonic_words = self.generate_mnemonic_from_entropy(entropy)
        
        # Generate keypair
        private_key, public_key, address = self.generate_keypair_from_mnemonic(mnemonic_words)
        
        # Create MemoryVault seed
        seed = MemoryVaultSeed(
            story_hash=story_hash,
            personal_elements=elements,
            normalized_story=self.normalize_story(story),
            entropy=entropy,
            mnemonic=mnemonic_words,
            private_key=private_key,
            public_key=public_key,
            address=address
        )
        
        return seed
    
    def recover_from_story(self, story: str) -> MemoryVaultSeed:
        """Recover MemoryVault seed from story"""
        return self.create_memory_vault_seed(story)
    
    def recover_from_mnemonic(self, mnemonic_phrase: str) -> MemoryVaultSeed:
        """Recover MemoryVault seed from mnemonic"""
        import mnemonic as mnemonic_module
        # Validate mnemonic
        if not mnemonic_module.Mnemonic('english').check(mnemonic_phrase):
            raise ValueError("Invalid mnemonic phrase")
        
        # Generate keypair
        private_key, public_key, address = self.generate_keypair_from_mnemonic(mnemonic_phrase)
        
        # Create a minimal seed (without story elements)
        seed = MemoryVaultSeed(
            story_hash="",  # Not available from mnemonic
            personal_elements=[],  # Not available from mnemonic
            normalized_story="",  # Not available from mnemonic
            entropy=b"",  # Not available from mnemonic
            mnemonic=mnemonic_phrase,
            private_key=private_key,
            public_key=public_key,
            address=address
        )
        
        return seed
    
    def validate_story_personalness(self, story: str) -> Dict[str, any]:
        """Validate how personal a story is"""
        elements = self.extract_personal_elements(story)
        
        # Calculate personalness score
        total_confidence = sum(element.confidence for element in elements)
        avg_confidence = total_confidence / len(elements) if elements else 0
        
        # Count element types
        element_types = {}
        for element in elements:
            element_types[element.element_type] = element_types.get(element.element_type, 0) + 1
        
        # Check for personal keywords
        story_lower = story.lower()
        personal_keyword_count = 0
        for keyword_list in self.personal_keywords.values():
            for keyword in keyword_list:
                if keyword in story_lower:
                    personal_keyword_count += 1
        
        return {
            'personal_elements_count': len(elements),
            'average_confidence': avg_confidence,
            'element_types': element_types,
            'personal_keywords_found': personal_keyword_count,
            'personalness_score': min(1.0, (len(elements) * avg_confidence + personal_keyword_count * 0.1) / 10),
            'recommendations': self._generate_recommendations(elements, personal_keyword_count)
        }
    
    def _generate_recommendations(self, elements: List[StoryElement], keyword_count: int) -> List[str]:
        """Generate recommendations for improving story personalness"""
        recommendations = []
        
        if len(elements) < 5:
            recommendations.append("Include more personal details like names, locations, and emotions")
        
        if keyword_count < 3:
            recommendations.append("Add more personal keywords like 'my', 'secret', 'first', 'family'")
        
        element_types = [e.element_type for e in elements]
        if 'name' not in element_types:
            recommendations.append("Include personal names (pets, family members, friends)")
        
        if 'location' not in element_types:
            recommendations.append("Include specific locations (rooms, houses, secret spots)")
        
        if 'emotion' not in element_types:
            recommendations.append("Include emotional details (how you felt, what you learned)")
        
        if 'action' not in element_types:
            recommendations.append("Include personal actions (what you did, created, discovered)")
        
        return recommendations

# Example usage and testing
def main():
    """Example usage of MemoryVault"""
    mv = MemoryVault()
    
    # Example personal story
    story = """
    When I was 8, my first pet was a goldfish named Bubbles because he always made 
    bubble sounds. I kept him in a secret spot behind my toy box in my room. One day, 
    I accidentally spilled my juice on the floor and had to hide it from my mom by 
    putting a blanket over it. That's when I learned that honesty is better than 
    hiding things, and I created my secret handshake with my sister using three 
    high-fives and a fist bump. Now whenever I feel stressed, I go to my secret spot 
    in the corner of my garden and remember that moment with Bubbles.
    """
    
    print("🔐 MemoryVault - Semantic Seed Phrase System")
    print("=" * 60)
    
    # Validate story personalness
    validation = mv.validate_story_personalness(story)
    print(f"📊 Story Personalness Score: {validation['personalness_score']:.2f}")
    print(f"🔍 Personal Elements Found: {validation['personal_elements_count']}")
    print(f"🏷️  Element Types: {validation['element_types']}")
    
    if validation['recommendations']:
        print("💡 Recommendations:")
        for rec in validation['recommendations']:
            print(f"   - {rec}")
    
    # Create MemoryVault seed
    try:
        seed = mv.create_memory_vault_seed(story)
        print(f"\n✅ MemoryVault Seed Created Successfully!")
        print(f"🏠 Address: {seed.address}")
        print(f"🗝️  Mnemonic: {seed.mnemonic}")
        print(f"📝 Story Hash: {seed.story_hash[:16]}...")
        print(f"🔍 Personal Elements: {len(seed.personal_elements)}")
        
        # Test recovery
        recovered_seed = mv.recover_from_story(story)
        print(f"\n🔄 Recovery Test: {'✅ PASSED' if recovered_seed.address == seed.address else '❌ FAILED'}")
        
    except Exception as e:
        print(f"❌ Error creating seed: {e}")

if __name__ == '__main__':
    main() 