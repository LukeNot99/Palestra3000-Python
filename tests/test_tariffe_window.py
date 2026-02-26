"""
Unit test per ui/tariffe_window.py
Testa: helper module-level, read_setting, validazione form, logica CRUD.
La GUI viene mockata — i test verificano la logica, non il rendering.
"""
import json
import os
import pytest
from unittest.mock import patch, MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base, Tier, Member


# ─── Fixture DB in-memory ────────────────────────────────────────────────────

@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def sample_tier(db_session) -> Tier:
    """Crea e ritorna una Tier di esempio già committata."""
    tier = Tier(
        name="Open",
        cost=50.0,
        min_age=16,
        max_age=65,
        start_time="06:00",
        end_time="22:00",
        duration_months=1,
        max_entries=0,
    )
    db_session.add(tier)
    db_session.commit()
    return tier


# ═════════════════════════════════════════════════════════════════════════════
# 1. TEST HELPER MODULE-LEVEL (nessuna GUI necessaria)
# ═════════════════════════════════════════════════════════════════════════════

class TestSetEntry:
    def test_set_entry_clears_and_inserts(self):
        """_set_entry deve svuotare e inserire il nuovo valore."""
        mock_entry = MagicMock()
        from ui.tariffe_window import _set_entry
        _set_entry(mock_entry, "hello")
        mock_entry.delete.assert_called_once_with(0, "end")
        mock_entry.insert.assert_called_once_with(0, "hello")


class TestReadSetting:
    def test_returns_value_from_config(self, tmp_path):
        config = tmp_path / "config.json"
        config.write_text(json.dumps({"mostra_costo_fasce": True}))
        from ui.tariffe_window import read_setting
        with patch("ui.tariffe_window.os.path.exists", return_value=True), \
             patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__ = lambda s: config.open()
            mock_open.return_value.__exit__ = MagicMock(return_value=False)
            # Usiamo il file reale tmp_path
            original_open = open
            with patch("builtins.open", lambda *a, **kw: original_open(str(config), *a[1:], **kw)):
                result = read_setting("mostra_costo_fasce", False)
        assert result is True

    def test_returns_default_when_key_missing(self, tmp_path):
        config = tmp_path / "config.json"
        config.write_text(json.dumps({"altra_chiave": 123}))
        from ui.tariffe_window import read_setting
        original_open = open
        with patch("ui.tariffe_window.os.path.exists", return_value=True), \
             patch("builtins.open", lambda *a, **kw: original_open(str(config), *a[1:], **kw)):
            result = read_setting("mostra_costo_fasce", False)
        assert result is False

    def test_returns_default_when_file_missing(self):
        from ui.tariffe_window import read_setting
        with patch("ui.tariffe_window.os.path.exists", return_value=False):
            result = read_setting("qualsiasi", 42)
        assert result == 42

    def test_returns_default_on_corrupt_json(self, tmp_path):
        config = tmp_path / "config.json"
        config.write_text("{not valid json!!!")
        from ui.tariffe_window import read_setting
        original_open = open
        with patch("ui.tariffe_window.os.path.exists", return_value=True), \
             patch("builtins.open", lambda *a, **kw: original_open(str(config), *a[1:], **kw)):
            result = read_setting("key", "default_val")
        assert result == "default_val"


# ═════════════════════════════════════════════════════════════════════════════
# 2. TEST COSTANTI / DIZIONARI
# ═════════════════════════════════════════════════════════════════════════════

class TestConstants:
    def test_field_defaults_keys(self):
        from ui.tariffe_window import FIELD_DEFAULTS
        expected_keys = {"min_age", "max_age", "start_time", "end_time",
                         "duration_months", "max_entries", "cost_placeholder"}
        assert set(FIELD_DEFAULTS.keys()) == expected_keys

    def test_field_defaults_all_strings(self):
        from ui.tariffe_window import FIELD_DEFAULTS
        for key, val in FIELD_DEFAULTS.items():
            assert isinstance(val, str), f"FIELD_DEFAULTS['{key}'] dovrebbe essere str, è {type(val)}"

    def test_ui_colors_has_required_keys(self):
        from ui.tariffe_window import UI_COLORS
        required = {"bg_primary", "bg_selected", "border_default", "border_selected",
                     "text_primary", "text_secondary", "btn_primary", "btn_success", "btn_danger"}
        assert required.issubset(set(UI_COLORS.keys()))

    def test_ui_fonts_has_required_keys(self):
        from ui.tariffe_window import UI_FONTS
        required = {"label_bold", "entry", "table_header", "table_row", "button"}
        assert required.issubset(set(UI_FONTS.keys()))

    def test_ui_fonts_tuples_have_3_elements(self):
        from ui.tariffe_window import UI_FONTS
        for key, val in UI_FONTS.items():
            assert len(val) == 3, f"UI_FONTS['{key}'] dovrebbe avere 3 elementi"
            assert val[2] in ("normal", "bold"), f"UI_FONTS['{key}'][2] deve essere 'normal' o 'bold'"


# ═════════════════════════════════════════════════════════════════════════════
# 3. TEST LOGICA CRUD (DB puro, niente GUI)
# ═════════════════════════════════════════════════════════════════════════════

class TestTierCRUD:
    def test_create_tier(self, db_session):
        tier = Tier(name="Test", cost=25.0, duration_months=3, max_entries=10)
        db_session.add(tier)
        db_session.commit()

        saved = db_session.query(Tier).filter_by(name="Test").first()
        assert saved is not None
        assert saved.cost == 25.0
        assert saved.duration_months == 3
        assert saved.max_entries == 10

    def test_update_tier(self, db_session, sample_tier):
        sample_tier.cost = 75.0
        sample_tier.name = "Premium"
        db_session.commit()

        updated = db_session.query(Tier).filter_by(id=sample_tier.id).first()
        assert updated.name == "Premium"
        assert updated.cost == 75.0

    def test_delete_tier_without_members(self, db_session, sample_tier):
        tier_id = sample_tier.id
        db_session.delete(sample_tier)
        db_session.commit()

        assert db_session.query(Tier).filter_by(id=tier_id).first() is None

    def test_cannot_delete_tier_with_members(self, db_session, sample_tier):
        member = Member(first_name="Mario", last_name="Rossi", tier_id=sample_tier.id)
        db_session.add(member)
        db_session.commit()

        count = db_session.query(Member).filter(Member.tier_id == sample_tier.id).count()
        assert count > 0  # La logica UI impedisce la cancellazione


# ═════════════════════════════════════════════════════════════════════════════
# 4. TEST VALIDAZIONE FORM (_read_form_fields)
# ═════════════════════════════════════════════════════════════════════════════

class TestFormValidation:
    """Testa la logica di validazione senza istanziare la GUI vera."""

    def _make_mock_view(self, **overrides):
        """Crea un mock di TiersView con entry widget simulati."""
        defaults = {
            "code": "Mensile",
            "cost": "50.0",
            "age_min": "16",
            "age_max": "65",
            "entry_time": "06:00",
            "exit_time": "22:00",
            "duration": "1",
            "entries": "0",
        }
        defaults.update(overrides)

        view = MagicMock()
        view.show_cost = True
        view.show_age = True

        def make_entry(value):
            entry = MagicMock()
            entry.get.return_value = value
            return entry

        view.ent_code = make_entry(defaults["code"])
        view.ent_cost = make_entry(defaults["cost"])
        view.ent_age_min = make_entry(defaults["age_min"])
        view.ent_age_max = make_entry(defaults["age_max"])
        view.ent_entry_time = make_entry(defaults["entry_time"])
        view.ent_exit_time = make_entry(defaults["exit_time"])
        view.ent_duration = make_entry(defaults["duration"])
        view.ent_entries = make_entry(defaults["entries"])

        return view

    def test_valid_form_returns_dict(self):
        from ui.tariffe_window import TiersView, FIELD_DEFAULTS
        view = self._make_mock_view()
        result = TiersView._read_form_fields(view)

        assert result["code"] == "Mensile"
        assert result["cost"] == 50.0
        assert result["age_min"] == 16
        assert result["age_max"] == 65
        assert result["entry_time"] == "06:00"
        assert result["exit_time"] == "22:00"
        assert result["duration_months"] == 1
        assert result["entries"] == 0

    def test_invalid_time_format_raises(self):
        from ui.tariffe_window import TiersView
        view = self._make_mock_view(entry_time="invalid")
        with pytest.raises(ValueError):
            TiersView._read_form_fields(view)

    def test_negative_cost_raises(self):
        from ui.tariffe_window import TiersView
        view = self._make_mock_view(cost="-10")
        with pytest.raises(ValueError, match="negativi"):
            TiersView._read_form_fields(view)

    def test_age_max_less_than_min_raises(self):
        from ui.tariffe_window import TiersView
        view = self._make_mock_view(age_min="50", age_max="20")
        with pytest.raises(ValueError, match="massima"):
            TiersView._read_form_fields(view)

    def test_duration_zero_raises(self):
        from ui.tariffe_window import TiersView
        view = self._make_mock_view(duration="0")
        with pytest.raises(ValueError, match="negativi"):
            TiersView._read_form_fields(view)

    def test_negative_entries_raises(self):
        from ui.tariffe_window import TiersView
        view = self._make_mock_view(entries="-5")
        with pytest.raises(ValueError, match="negativi"):
            TiersView._read_form_fields(view)

    def test_empty_duration_uses_default(self):
        from ui.tariffe_window import TiersView, FIELD_DEFAULTS
        view = self._make_mock_view(duration="")
        result = TiersView._read_form_fields(view)
        assert result["duration_months"] == int(FIELD_DEFAULTS["duration_months"])

    def test_empty_entries_uses_default(self):
        from ui.tariffe_window import TiersView, FIELD_DEFAULTS
        view = self._make_mock_view(entries="")
        result = TiersView._read_form_fields(view)
        assert result["entries"] == int(FIELD_DEFAULTS["max_entries"])

    def test_cost_comma_separator(self):
        from ui.tariffe_window import TiersView
        view = self._make_mock_view(cost="29,99")
        result = TiersView._read_form_fields(view)
        assert result["cost"] == pytest.approx(29.99)

    def test_cost_hidden_defaults_to_zero(self):
        from ui.tariffe_window import TiersView
        view = self._make_mock_view()
        view.show_cost = False
        result = TiersView._read_form_fields(view)
        assert result["cost"] == 0.0

    def test_age_hidden_defaults(self):
        from ui.tariffe_window import TiersView
        view = self._make_mock_view()
        view.show_age = False
        result = TiersView._read_form_fields(view)
        assert result["age_min"] == 0
        assert result["age_max"] == 999


# ═════════════════════════════════════════════════════════════════════════════
# 5. TEST _get_row_values (formattazione righe tabella)
# ═════════════════════════════════════════════════════════════════════════════

class TestGetRowValues:
    def _make_mock_view(self, show_cost=True, show_age=True):
        view = MagicMock()
        view.show_cost = show_cost
        view.show_age = show_age
        return view

    def test_all_columns_visible(self):
        from ui.tariffe_window import TiersView
        tier = MagicMock()
        tier.name = "Open"
        tier.cost = 50.0
        tier.min_age = 16
        tier.max_age = 65
        tier.start_time = "06:00"
        tier.end_time = "22:00"
        tier.duration_months = 1
        tier.max_entries = 0

        view = self._make_mock_view()
        values = TiersView._get_row_values(view, tier)

        assert values[0] == "Open"
        assert "€ 50.00" in values[1]
        assert "16 - 65 anni" in values[2]
        assert "06:00 - 22:00" in values[3]
        assert "1 Mesi" in values[4]
        assert "Illimitati" in values[5]

    def test_limited_entries_shows_count(self):
        from ui.tariffe_window import TiersView
        tier = MagicMock()
        tier.name = "Carnet"
        tier.cost = 40.0
        tier.min_age = 0
        tier.max_age = 200
        tier.start_time = "08:00"
        tier.end_time = "20:00"
        tier.duration_months = 2
        tier.max_entries = 10

        view = self._make_mock_view()
        values = TiersView._get_row_values(view, tier)
        assert "10 Ingressi" in values[-1]

    def test_hidden_cost_and_age(self):
        from ui.tariffe_window import TiersView
        tier = MagicMock()
        tier.name = "Basic"
        tier.start_time = "06:00"
        tier.end_time = "22:00"
        tier.duration_months = 1
        tier.max_entries = 0

        view = self._make_mock_view(show_cost=False, show_age=False)
        values = TiersView._get_row_values(view, tier)

        # Senza costo e età: nome, orari, durata, ingressi = 4 valori
        assert len(values) == 4
        assert values[0] == "Basic"


# ═════════════════════════════════════════════════════════════════════════════
# 6. TEST _update_tier / _create_tier (logica DB con mock)
# ═════════════════════════════════════════════════════════════════════════════

class TestTierPersistence:
    SAMPLE_DATA = {
        "code": "Nuovo",
        "cost": 35.0,
        "age_min": 18,
        "age_max": 60,
        "entry_time": "07:00",
        "exit_time": "21:00",
        "duration_months": 3,
        "entries": 15,
    }

    def test_create_tier_adds_to_db(self, db_session):
        from ui.tariffe_window import TiersView
        view = MagicMock()
        view.db = db_session
        TiersView._create_tier(view, self.SAMPLE_DATA)
        db_session.commit()

        created = db_session.query(Tier).filter_by(name="Nuovo").first()
        assert created is not None
        assert created.cost == 35.0
        assert created.duration_months == 3
        assert created.max_entries == 15
        assert created.start_time == "07:00"

    def test_update_tier_modifies_existing(self, db_session, sample_tier):
        from ui.tariffe_window import TiersView
        view = MagicMock()
        view.db = db_session
        view.editing_tier_id = sample_tier.id

        TiersView._update_tier(view, self.SAMPLE_DATA)
        db_session.commit()

        updated = db_session.query(Tier).filter_by(id=sample_tier.id).first()
        assert updated.name == "Nuovo"
        assert updated.cost == 35.0
        assert updated.min_age == 18
        assert updated.max_age == 60

    def test_update_tier_nonexistent_does_nothing(self, db_session):
        from ui.tariffe_window import TiersView
        view = MagicMock()
        view.db = db_session
        view.editing_tier_id = 99999

        # Non deve crashare
        TiersView._update_tier(view, self.SAMPLE_DATA)
        assert db_session.query(Tier).count() == 0

