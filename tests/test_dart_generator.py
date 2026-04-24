"""
tests/test_dart_generator.py – tests for the proto → Dart generator.

Run with:
    python -m pytest tests/ -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from parse_proto import parse_proto  # noqa: E402
from generate_dart import generate as gen_dart  # noqa: E402

PROTO_FILE = Path(__file__).parent.parent / "contracts" / "user" / "v1" / "user.proto"
BILLING_PROTO = Path(__file__).parent.parent / "contracts" / "billing" / "v1" / "billing.proto"
INVENTORY_PROTO = Path(__file__).parent.parent / "contracts" / "inventory" / "v1" / "inventory.proto"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def user_ast():
    return parse_proto(str(PROTO_FILE))


@pytest.fixture(scope="module")
def billing_ast():
    return parse_proto(str(BILLING_PROTO))


@pytest.fixture(scope="module")
def inventory_ast():
    return parse_proto(str(INVENTORY_PROTO))


# ---------------------------------------------------------------------------
# Dart generator – user contract
# ---------------------------------------------------------------------------


class TestGenerateDartUser:
    def test_package_comment_present(self, user_ast):
        output = gen_dart(user_ast)
        assert "user.v1" in output

    def test_class_definitions(self, user_ast):
        output = gen_dart(user_ast)
        assert "class User {" in output
        assert "class CreateUserCommand {" in output
        assert "class GetUserQuery {" in output

    def test_string_fields_use_dart_string(self, user_ast):
        output = gen_dart(user_ast)
        assert "final String email" in output
        assert "final String id" in output

    def test_const_constructor_present(self, user_ast):
        output = gen_dart(user_ast)
        assert "const User(" in output
        assert "const CreateUserCommand(" in output

    def test_from_json_factory_present(self, user_ast):
        output = gen_dart(user_ast)
        assert "factory User.fromJson" in output
        assert "factory CreateUserCommand.fromJson" in output

    def test_to_json_method_present(self, user_ast):
        output = gen_dart(user_ast)
        assert "Map<String, dynamic> toJson()" in output

    def test_required_named_params(self, user_ast):
        output = gen_dart(user_ast)
        assert "required this.email" in output
        assert "required this.id" in output

    def test_output_to_file(self, user_ast, tmp_path):
        out = tmp_path / "user_models.dart"
        content = gen_dart(user_ast)
        out.write_text(content, encoding="utf-8")
        assert out.exists()
        assert "class User" in out.read_text()


# ---------------------------------------------------------------------------
# Dart generator – billing contract
# ---------------------------------------------------------------------------


class TestGenerateDartBilling:
    def test_invoice_class_present(self, billing_ast):
        output = gen_dart(billing_ast)
        assert "class Invoice {" in output

    def test_double_field_type(self, billing_ast):
        output = gen_dart(billing_ast)
        assert "final double amount" in output

    def test_event_classes_present(self, billing_ast):
        output = gen_dart(billing_ast)
        assert "class InvoiceCreated {" in output
        assert "class InvoicePaid {" in output

    def test_command_classes_present(self, billing_ast):
        output = gen_dart(billing_ast)
        assert "class CreateInvoiceCommand {" in output
        assert "class PayInvoiceCommand {" in output


# ---------------------------------------------------------------------------
# Dart generator – inventory contract
# ---------------------------------------------------------------------------


class TestGenerateDartInventory:
    def test_item_class_present(self, inventory_ast):
        output = gen_dart(inventory_ast)
        assert "class Item {" in output

    def test_int_field_type(self, inventory_ast):
        output = gen_dart(inventory_ast)
        assert "final int quantity" in output

    def test_event_classes_present(self, inventory_ast):
        output = gen_dart(inventory_ast)
        assert "class ItemAdded {" in output
        assert "class StockUpdated {" in output


# ---------------------------------------------------------------------------
# New contracts – parse_proto sanity checks
# ---------------------------------------------------------------------------


class TestBillingProto:
    def test_package(self, billing_ast):
        assert billing_ast["package"] == "billing.v1"

    def test_message_names(self, billing_ast):
        names = [m["name"] for m in billing_ast["messages"]]
        assert "Invoice" in names
        assert "CreateInvoiceCommand" in names
        assert "InvoiceCreated" in names
        assert "InvoicePaid" in names

    def test_invoice_fields(self, billing_ast):
        invoice = next(m for m in billing_ast["messages"] if m["name"] == "Invoice")
        field_names = [f["name"] for f in invoice["fields"]]
        assert "id" in field_names
        assert "user_id" in field_names
        assert "amount" in field_names
        assert "currency" in field_names
        assert "status" in field_names

    def test_amount_is_double(self, billing_ast):
        invoice = next(m for m in billing_ast["messages"] if m["name"] == "Invoice")
        types = {f["name"]: f["type"] for f in invoice["fields"]}
        assert types["amount"] == "double"


class TestInventoryProto:
    def test_package(self, inventory_ast):
        assert inventory_ast["package"] == "inventory.v1"

    def test_message_names(self, inventory_ast):
        names = [m["name"] for m in inventory_ast["messages"]]
        assert "Item" in names
        assert "AddItemCommand" in names
        assert "ItemAdded" in names
        assert "StockUpdated" in names

    def test_item_fields(self, inventory_ast):
        item = next(m for m in inventory_ast["messages"] if m["name"] == "Item")
        field_names = [f["name"] for f in item["fields"]]
        assert "id" in field_names
        assert "name" in field_names
        assert "quantity" in field_names

    def test_quantity_is_int32(self, inventory_ast):
        item = next(m for m in inventory_ast["messages"] if m["name"] == "Item")
        types = {f["name"]: f["type"] for f in item["fields"]}
        assert types["quantity"] == "int32"
