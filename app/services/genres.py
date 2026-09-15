"""
Жанры для автосборки. iTunes на «названия жанров» отдаёт плейлисты-сборники,
поэтому под каждый жанр заданы РЕАЛЬНЫЕ исполнители — приходят настоящие песни
нужного жанра и языка. Списки большие, чтобы хватало на много раундов.
"""

GENRE_QUERIES = {
    "pop": [
        "Taylor Swift", "Ed Sheeran", "Dua Lipa", "The Weeknd", "Ariana Grande",
        "Bruno Mars", "Katy Perry", "Maroon 5", "Justin Bieber", "Lady Gaga",
        "Rihanna", "Adele", "Sam Smith", "Sia", "Charlie Puth", "Shawn Mendes",
        "Billie Eilish", "Harry Styles", "Coldplay", "OneRepublic", "P!nk",
        "Miley Cyrus", "Selena Gomez", "Camila Cabello", "Doja Cat", "Lorde",
    ],
    "rock": [
        "Queen", "Nirvana", "Linkin Park", "Coldplay", "Imagine Dragons",
        "AC/DC", "The Beatles", "Red Hot Chili Peppers", "Metallica", "Green Day",
        "Foo Fighters", "Guns N Roses", "U2", "The Rolling Stones", "Pink Floyd",
        "Led Zeppelin", "Radiohead", "Muse", "Arctic Monkeys", "The Killers",
        "Bon Jovi", "Aerosmith", "Pearl Jam", "System of a Down", "Paramore",
    ],
    "rap": [
        "Eminem", "Drake", "Kanye West", "Travis Scott", "Kendrick Lamar",
        "Post Malone", "50 Cent", "Snoop Dogg", "Jay-Z", "Nicki Minaj",
        "Cardi B", "Lil Wayne", "Tyler The Creator", "J. Cole", "Nas",
        "Dr. Dre", "Ice Cube", "Wiz Khalifa", "Macklemore", "Logic",
        "A$AP Rocky", "Future", "21 Savage", "Megan Thee Stallion", "DaBaby",
    ],
    "electro": [
        "Avicii", "David Guetta", "Calvin Harris", "Marshmello", "Skrillex",
        "Daft Punk", "Martin Garrix", "The Chainsmokers", "Deadmau5", "Zedd",
        "Kygo", "Alan Walker", "Tiesto", "Swedish House Mafia", "Diplo",
        "Major Lazer", "Flume", "Disclosure", "ODESZA", "Galantis",
    ],
    "russian": [
        "Zemfira", "Kino Viktor Tsoi", "Leningrad", "Bi-2", "Splean",
        "Zveri", "MakSim", "Dima Bilan", "Mumiy Troll", "DDT",
        "Nautilus Pompilius", "Alla Pugacheva", "Valeriy Meladze", "Ani Lorak",
        "Polina Gagarina", "Sergey Lazarev", "Nyusha", "Vremya i Steklo",
        "Ivan Dorn", "Monatik", "LOBODA", "Egor Kreed", "Basta", "Oxxxymiron",
    ],
    "80s": [
        "Michael Jackson", "Madonna", "Queen", "Depeche Mode", "a-ha",
        "Duran Duran", "Prince", "Whitney Houston", "Cyndi Lauper", "Bon Jovi",
        "Tears for Fears", "Eurythmics", "The Police", "Phil Collins", "Bee Gees",
        "Wham", "Culture Club", "Billy Idol", "Toto", "Journey",
    ],
    "90s": [
        "Nirvana", "Backstreet Boys", "Spice Girls", "Britney Spears",
        "Oasis", "Aerosmith", "TLC", "Radiohead", "Mariah Carey", "Celine Dion",
        "Ace of Base", "Aqua", "Blur", "Green Day", "Red Hot Chili Peppers",
        "Whitney Houston", "Boyz II Men", "Spice Girls", "Savage Garden", "Blink-182",
    ],
    "soundtrack": [
        "Hans Zimmer", "John Williams", "Disney soundtrack", "Queen soundtrack",
        "Elton John Lion King", "Frozen soundtrack", "James Bond theme",
        "Star Wars soundtrack", "Pirates of the Caribbean", "Harry Potter soundtrack",
        "Titanic soundtrack", "Bohemian Rhapsody soundtrack", "La La Land",
        "Greatest Showman", "Encanto soundtrack", "Moana soundtrack",
    ],
}

GENRE_LABELS = {
    "pop": "Поп", "rock": "Рок", "rap": "Рэп / Хип-хоп", "electro": "Электроника",
    "russian": "Русская музыка", "80s": "Хиты 80-х", "90s": "Хиты 90-х",
    "soundtrack": "Саундтреки", "mixed": "Микс",
}
