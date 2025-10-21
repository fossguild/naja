#!/usr/bin/env python3
#
#   Copyright (c) 2023, Monaco F. J. <monaco@usp.br>
#
#   This file is part of Naja.
#
#   Naja is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""UI subsystems for menu handling, dialogs, and command conversion."""

from .ui_system import UISystem
from .menu_handler import MenuHandler, StartDecision
from .settings_handler import SettingsHandler, SettingsResult
from .dialog_handler import DialogHandler, ResetDecision, GameOverDecision
from .command_converter import CommandConverter
from .settings_applicator import SettingsApplicator

__all__ = [
    "UISystem",
    "MenuHandler",
    "StartDecision",
    "SettingsHandler",
    "SettingsResult",
    "DialogHandler",
    "ResetDecision",
    "GameOverDecision",
    "CommandConverter",
    "SettingsApplicator",
]
