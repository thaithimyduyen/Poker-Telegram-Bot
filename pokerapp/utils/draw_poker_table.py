import io
from typing import List

import matplotlib.pyplot as plt
import numpy as np

from pokerapp.entity.player import Player

oval_center = (0, 0)
oval_a = 3
oval_b = 2
oval_angle = 0
circle_radius = 0.5
oval_offset = 0.2


def __draw_oval(ax, center, a, b, angle, color='black', linewidth=1, linestyle='solid'):
    t = np.linspace(0, 2 * np.pi, 100)
    x = center[0] + a * np.cos(t) * np.cos(angle) - b * np.sin(t) * np.sin(angle)
    y = center[1] + a * np.cos(t) * np.sin(angle) + b * np.sin(t) * np.cos(angle)
    ax.plot(x, y, color=color, linewidth=linewidth, linestyle=linestyle)


def __draw_circle(ax, center, radius, color='black', linewidth=1):
    t = np.linspace(0, 2 * np.pi, 100)
    x = center[0] + radius * np.cos(t)
    y = center[1] + radius * np.sin(t)
    ax.plot(x, y, color=color, linewidth=linewidth)


def draw_poker_table(players: List[Player], current_player: Player):
    assert 1 <= len(players) <= 6

    fig, ax = plt.subplots()

    # draw outer layer of the oval
    __draw_oval(ax, oval_center, oval_a + oval_offset, oval_b + oval_offset, oval_angle, linestyle='dashed')

    # draw the table
    __draw_oval(ax, oval_center, 2 - oval_offset, 1 - oval_offset, oval_angle)

    # draw the circles (players) around the table. The distance between the players is equal.
    for i, player in enumerate(players):
        angle = 2 * np.pi * i / len(players)
        circle_center = (oval_center[0] + (oval_a - circle_radius) * np.cos(angle),
                         oval_center[1] + (oval_b - circle_radius) * np.sin(angle))
        color = player == current_player and 'red' or 'black'
        __draw_circle(ax, circle_center, circle_radius, color=color)

    ax.set_aspect('equal', adjustable='box')
    plt.axis('off')

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)

    return buffer
