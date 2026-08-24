"""How numbers read on the page.

A report is read by someone who did not write it, so a figure that is
arithmetically defensible and visually confusing is still a defect: the reader
cannot tell an artefact of rounding from a bug in the pipeline, and either
guess costs them trust in every other number on the page.
"""

from __future__ import annotations

from ranking.publish import format


class TestPercent:
    def test_a_negative_number_too_small_to_show_prints_as_zero(self) -> None:
        """A fund that trailed the CDI by a ten-thousandth of a percent rounds
        to zero at two places. Printed with the sign it reads as `-0.00%`, a
        quantity that does not exist, and the reader is entitled to read that
        as a broken formatter rather than as a fund that matched its index."""
        assert format.percent(-0.0000001) == "0.00%"

    def test_a_negative_number_large_enough_to_show_keeps_its_sign(self) -> None:
        assert format.percent(-0.0031) == "-0.31%"

    def test_the_rule_follows_the_places_asked_for(self) -> None:
        """Rounding to zero depends on how many places are printed, so the
        suppression has to be decided after rounding, not before."""
        assert format.percent(-0.00001, 2) == "0.00%"
        assert format.percent(-0.00001, 3) == "-0.001%"

    def test_zero_itself_is_unchanged(self) -> None:
        assert format.percent(0.0) == "0.00%"

    def test_positive_numbers_are_untouched(self) -> None:
        assert format.percent(0.0004, 3) == "0.040%"
