import monpy        

@monpy.Many.lift(True, False)
def f(x, y): return x + y

def g(x, y, z): return (x * z) + (y * z)

def main():
    xs = monpy.Many(0, 1)
    print(f(xs, 2)) # (2, 3)

    print(monpy.Many.do(
        x = lambda s: monpy.Many(0, 2),
        y = lambda s: monpy.Many(0, 1),
        z = lambda s: monpy.Many.wrap(g(s.x, s.y, -1))
    ).map(lambda s: s.z)) # (0, -1, -2, -3)

    print(monpy.flatten(monpy.Many,
        monpy.Many(
            0,
            monpy.Many(
                1,
                2
            ),
            monpy.Many(
                3,
                4
            )
        )
    )) # (0, 1, 2, 3, 4)

if __name__ == "__main__":
    main()