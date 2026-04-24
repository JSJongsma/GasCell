# FitnessEvaluator.py
# this class will evaluate the 'fitness' of a geometry, on the basis of the distance to the exit hole of the final reflection, after N iterations.
# the smaller the distance, the higher the fitness d=\sqrt{(x_{exit}-x_{final})^2+(y_{exit}-y_{final})^2}.

import sys
import os

# Pad-instellingen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import math
from Math.vector import Vector
from Results.track_memory import TrackMemory
from Physics.Physics import PhysicsUtils


class FitnessEvaluator:
    def __init__(self, target_reflections, hole_diameter=0.4, entry_hole_diameter=0.4, initial_beam_diameter_cm=None):
        self.target_reflections = target_reflections
        self.target_u = 1.2
        self.target_v = 0.0
        self.hole_diameter = hole_diameter
        self.hole_radius = self.hole_diameter / 2.0

        self.entry_hole_u = -1.2
        self.entry_hole_v = 0.0
        self.entry_hole_diameter = entry_hole_diameter
        self.entry_hole_radius = self.entry_hole_diameter / 2.0

        self.initial_beam_diameter_cm = entry_hole_diameter if initial_beam_diameter_cm is None else initial_beam_diameter_cm

    def _find_hole_state(self, states):
        # Zoek naar een staat op M2 binnen de hole radius
        for state in states:
            if state.mirror_name == "M2":
                du = state.u - self.target_u
                dv = state.v - self.target_v
                if du * du + dv * dv <= self.hole_radius**2:
                    return state
        return None

    def _has_invalid_hole_reflection(self, states):
        for state in states:
            if getattr(state, 'event_type', 'reflection') != 'reflection':
                continue
            mirror_name = state.mirror_name.lower()
            if mirror_name == 'm1':
                du = state.u - self.entry_hole_u
                dv = state.v - self.entry_hole_v
                if du * du + dv * dv <= self.entry_hole_radius**2:
                    return True
            if mirror_name == 'm2':
                du = state.u - self.target_u
                dv = state.v - self.target_v
                if du * du + dv * dv <= self.hole_radius**2:
                    return True
        return False

    @staticmethod
    def _circle_intersection_area(r1, r2, d):
        if d >= r1 + r2:
            return 0.0
        if d <= abs(r1 - r2):
            return math.pi * min(r1, r2)**2

        r1_sq = r1 * r1
        r2_sq = r2 * r2
        alpha = 2.0 * math.acos((d*d + r1_sq - r2_sq) / (2.0 * d * r1))
        beta = 2.0 * math.acos((d*d + r2_sq - r1_sq) / (2.0 * d * r2))

        return 0.5 * (r1_sq * (alpha - math.sin(alpha)) + r2_sq * (beta - math.sin(beta)))

    def _beam_leak_penalty(self, states):
        """
        Bereken een continue straallek-penalty op basis van overlapgebied.
        Deze penalty is groter als meer van de beam overlapt met een gat of over de spiegelrand glijdt.
        """
        mirror_radius = 2.54  # cm, van TwoGrid(5.08, 5.08, 0.1) u_range/2
        initial_beam_diameter_cm = self.initial_beam_diameter_cm
        wavelength_mm = 1654e-6  # mm

        start_pos = Vector(0, 20, 25.0)
        current_pos = start_pos
        cumulative_path_cm = 0.0
        total_leak_area = 0.0

        for i, state in enumerate(states):
            if getattr(state, 'event_type', 'reflection') != 'reflection':
                continue

            segment_length = (state.position - current_pos).norm()
            cumulative_path_cm += segment_length
            current_pos = state.position

            beam_diameter_mm = PhysicsUtils.calculate_beam_diameter(
                wavelength=wavelength_mm,
                beam_diameter=initial_beam_diameter_cm * 10.0,
                distance_traveled=cumulative_path_cm * 10.0
            )
            beam_radius_cm = (beam_diameter_mm / 2.0) / 10.0
            beam_area = math.pi * beam_radius_cm * beam_radius_cm

            dist_to_center = math.hypot(state.u, state.v)
            mirror_overlap = self._circle_intersection_area(beam_radius_cm, mirror_radius, dist_to_center)
            total_leak_area += max(0.0, beam_area - mirror_overlap)

            if i < len(states) - 1:
                mirror_name = state.mirror_name.lower()
                if mirror_name == 'm1':
                    du = state.u - self.entry_hole_u
                    dv = state.v - self.entry_hole_v
                    dist_to_hole = math.hypot(du, dv)
                    total_leak_area += self._circle_intersection_area(beam_radius_cm, self.entry_hole_radius, dist_to_hole)
                elif mirror_name == 'm2':
                    du = state.u - self.target_u
                    dv = state.v - self.target_v
                    dist_to_hole = math.hypot(du, dv)
                    total_leak_area += self._circle_intersection_area(beam_radius_cm, self.hole_radius, dist_to_hole)

        return total_leak_area

    def calculate_score(self, track_memory):
        states = track_memory.memory
        if not states:
            return -1e12

        if self._has_invalid_hole_reflection(states):
            return -1e11

        # Meet echte reflecties en eventuele hole exit als eindgebeurtenis.
        reflection_count = sum(
            1 for state in states if getattr(state, 'event_type', 'reflection') == 'reflection'
        )
        hole_exit_state = next(
            (state for state in states if getattr(state, 'event_type', None) == 'hole_exit'),
            None
        )
        total_path_hits = reflection_count + (1 if hole_exit_state else 0)
        last_state = hole_exit_state if hole_exit_state else states[-1]

        # 1. CRUCIALE CHECK: Een valide geometrie mag alleen eindigen op M2.
        if last_state.mirror_name.lower() != "m2":
            return -5e9

        # Bonus voor correcte cycli: alleen paden met 3n+1 hits zijn echt geldig
        cycle_bonus = 0
        if total_path_hits >= 1 and total_path_hits % 3 == 1:
            n_circulations = (total_path_hits - 1) // 3
            cycle_bonus = 1e8 + (3e7 * n_circulations)

        # 2. Check of we het gat geraakt hebben (of in de buurt zijn)
        du = last_state.u - self.target_u
        dv = last_state.v - self.target_v
        dist = math.sqrt(du**2 + dv**2)

        # Basis score: afstand tot het gat.
        score = -dist * 1_000_000

        # 3. Bounce-Target Check
        bounce_diff = self.target_reflections - total_path_hits
        if bounce_diff > 0:
            score -= 1e7 * bounce_diff**2

        if total_path_hits == self.target_reflections:
            score += 5e7

        if total_path_hits > self.target_reflections:
            score -= (total_path_hits - self.target_reflections) * 150_000

        # 3n+1 bonus voor circulaties die op M2 eindigen
        score += cycle_bonus

        # Expliciete beloning voor een hole-exit versus een normale M2-reflectie.
        if hole_exit_state is not None:
            score += 7e8
            if dist <= self.hole_radius:
                score += (self.hole_radius - dist) * 3e8
                if dist <= self.hole_radius * 0.5:
                    score += 2e8
        else:
            if last_state.mirror_name.lower() == "m2":
                score += 6e7
                if dist <= self.hole_radius:
                    score += (self.hole_radius - dist) * 5e7
                else:
                    overflow = dist - self.hole_radius
                    score -= 3e8
                    score -= overflow * 3e8
                    score -= (overflow**2) * 4e8

        leak_area = self._beam_leak_penalty(states)
        if leak_area > 0.0:
            score -= 1e7 + 3e8 * leak_area

        return score