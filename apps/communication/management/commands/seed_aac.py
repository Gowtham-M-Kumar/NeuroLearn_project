from django.core.management.base import BaseCommand
from apps.communication.models import AACCategory, AACSymbol

class Command(BaseCommand):
    help = 'Seeds initial AAC categories and symbols'

    def handle(self, *args, **options):
        # 1. Categories
        cats = [
            {'name': 'Food / Drink', 'color': '#FCD34D', 'icon': 'restaurant', 'order': 1},
            {'name': 'Emotions', 'color': '#FBCFE8', 'icon': 'sentiment_satisfied', 'order': 2},
            {'name': 'Actions', 'color': '#34D399', 'icon': 'directions_run', 'order': 3},
            {'name': 'Things', 'color': '#FCD34D', 'icon': 'toys', 'order': 4},
            {'name': 'Places', 'color': '#60A5FA', 'icon': 'home', 'order': 5},
            {'name': 'People', 'color': '#FBCFE8', 'icon': 'people', 'order': 6},
            {'name': 'Alphabets', 'color': '#E5E7EB', 'icon': 'sort_by_alpha', 'order': 7},
            {'name': 'Numbers', 'color': '#E5E7EB', 'icon': 'looks_one', 'order': 8},
        ]

        created_cats = {}
        for c in cats:
            obj, created = AACCategory.objects.get_or_create(
                name=c['name'],
                defaults={'color': c['color'], 'icon': c['icon'], 'order': c['order']}
            )
            created_cats[c['name']] = obj
            
        self.stdout.write(self.style.SUCCESS(f'Categories seeded.'))

        # 2. Symbols
        symbols = [
            # Core Vocabulary (Layer 1)
            {'word': 'I', 'cat': 'People', 'action': 'Me', 'quick': True, 'color': 'yellow'},
            {'word': 'Want', 'cat': 'Actions', 'action': 'I want', 'quick': True, 'color': 'green'},
            {'word': 'Need', 'cat': 'Actions', 'action': 'I need', 'quick': True, 'color': 'green'},
            {'word': 'Where', 'cat': 'Places', 'action': 'Where is it?', 'quick': True, 'color': 'blue'},
            {'word': 'Why', 'cat': 'Places', 'action': 'Why?', 'quick': True, 'color': 'blue'},
            {'word': 'What', 'cat': 'Places', 'action': 'What is that?', 'quick': True, 'color': 'blue'},
            {'word': 'Mine', 'cat': 'People', 'action': 'That is mine', 'quick': True, 'color': 'yellow'},
            {'word': 'Like', 'cat': 'Actions', 'action': 'I like it', 'quick': True, 'color': 'green'},
            {'word': 'Go', 'cat': 'Actions', 'action': 'Lets go', 'quick': True, 'color': 'green'},
            {'word': 'Wait', 'cat': 'Actions', 'action': 'Wait please', 'quick': True, 'color': 'green'},
            {'word': 'Come', 'cat': 'Actions', 'action': 'Come here', 'quick': True, 'color': 'green'},
            {'word': 'Look', 'cat': 'Actions', 'action': 'Look at this', 'quick': True, 'color': 'green'},
            {'word': 'Listen', 'cat': 'Actions', 'action': 'Listen to this', 'quick': True, 'color': 'green'},
            {'word': 'Don\'t Like', 'cat': 'Actions', 'action': 'I do not like it', 'quick': True, 'color': 'red'},
            {'word': 'All Done', 'cat': 'Actions', 'action': 'I am all done', 'quick': True, 'color': 'red'},
            {'word': 'Again', 'cat': 'Actions', 'action': 'Do it again', 'quick': True, 'color': 'green'},
            
            # Legacy/Specific
            {'word': 'Yes', 'cat': 'Actions', 'action': 'Yes', 'quick': True, 'color': 'green'},
            {'word': 'No', 'cat': 'Actions', 'action': 'No', 'quick': True, 'color': 'red'},
            {'word': 'Help', 'cat': 'Actions', 'action': 'Help me', 'quick': True, 'color': 'blue'},
            {'word': 'Toilet', 'cat': 'Places', 'action': 'Bathroom', 'quick': True, 'color': 'yellow'},
            {'word': 'Hungry', 'cat': 'Emotions', 'action': 'Hungry', 'quick': True, 'color': 'orange'},
            {'word': 'Am', 'cat': 'Actions', 'action': 'I am', 'quick': True, 'color': 'green'},
            {'word': 'Thirsty', 'cat': 'Emotions', 'action': 'Thirsty', 'quick': True, 'color': 'blue'},

            # Food (Zone 3 examples)
            {'word': 'Apple', 'cat': 'Food / Drink', 'action': 'I want an apple'},
            {'word': 'Water', 'cat': 'Food / Drink', 'action': 'I want water'},
        ]
        
        # Add Alphabets
        import string
        for char in string.ascii_uppercase:
             symbols.append({
                 'word': char, 
                 'cat': 'Alphabets', 
                 'action': f'Letter {char}',
                 'color': 'grey'
             })
             
        # Add Numbers
        for i in range(10):
            symbols.append({
                'word': str(i), 
                'cat': 'Numbers', 
                'action': f'Number {i}', 
                'color': 'grey'
            })

        for s in symbols:
            cat = created_cats.get(s['cat'])
            if cat:
                AACSymbol.objects.get_or_create(
                    word=s['word'],
                    defaults={
                        'category': cat, 
                        'action_description': s['action'], 
                        'is_quick_need': s.get('quick', False),
                        'color_code': s.get('color', '')
                    }
                )

        self.stdout.write(self.style.SUCCESS(f'Symbols seeded.'))
