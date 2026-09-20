from src.effects import Particles


def test_particles_expire():
    particles = Particles(seed=1)
    particles.burst((0, 0), 10, (255, 255, 255), life=0.2)
    assert len(particles) == 10
    particles.update(0.5)
    assert len(particles) == 0


def test_particles_move_and_slow_down():
    particles = Particles(seed=1)
    particles.spawn((0, 0), (100, 0), 1.0, (255, 255, 255), 3)
    particles.update(0.1)
    item = particles.items[0]
    assert item["pos"].x > 0
    assert item["vel"].x < 100


def test_particle_budget_is_capped():
    particles = Particles(limit=30, seed=1)
    for _ in range(10):
        particles.burst((0, 0), 20, (255, 255, 255), life=5)
    assert len(particles) == 30
