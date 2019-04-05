from PIL import Image

from local_data import sweeper_map

def export_image(filename):
    img = Image.new('RGB', (2000, 2000), "white")  # <--
    # OR  Image.new('RGB', img1.size, "white")
    cmap = {-10: (255, 255, 255),
            -9: (255, 0, 0),
            -8: (255, 255, 0),
            -1: (150, 150, 150),
            0: (220, 220, 220),
            1: (160, 200, 160),
            2: (130, 200, 130),
            3: (100, 200, 100),
            4: (70, 200, 70),
            5: (40, 200, 40),
            6: (20, 200, 20),
            7: (0, 200, 0),
            8: (0, 255, 0),
            9: (100, 50, 0),
            10: (255, 150, 150),
            11: (0, 0, 0),
            12: (0, 0, 255),
            13: (0, 100, 255)}
    long_array = []
    for j in range(2000):  # row (y)
        for i in range(2000):  # column (x)
            long_array.append(sweeper_map[i][j])
    data = [cmap[i] for i in long_array]
    img.putdata(data)
    # img.show()
    img.save(filename)

