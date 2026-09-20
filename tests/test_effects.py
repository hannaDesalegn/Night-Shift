import pygame

from src.effects import Overlays, Particles, ScreenShake


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


def test_screen_shake_decays_to_zero():
    shake = ScreenShake(seed=2)
    shake.add(1.0)
    assert shake.offset(0.3).length() > 0
    shake.update(2.0)
    assert shake.trauma == 0
    assert shake.offset(0.3) == pygame.Vector2()


def test_screen_shake_trauma_is_clamped():
    shake = ScreenShake(seed=2)
    for _ in range(5):
        shake.add(0.5)
    assert shake.trauma == 1.0


def test_damage_flash_fades():
    overlays = Overlays((320, 200))
    overlays.hit()
    assert overlays.flash == 1.0
    overlays.update(1.0)
    assert overlays.flash == 0.0
