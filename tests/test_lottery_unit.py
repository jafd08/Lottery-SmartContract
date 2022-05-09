from brownie import Lottery, accounts, network, config, exceptions
from scripts.deploy_lottery import deploy_lottery
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    fund_with_link,
    get_account,
    get_contract,
)
from web3 import Web3
import pytest


def test_get_entrance_fee():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lott = deploy_lottery()
    # Act
    # initial value 2000..00 = $2000 eth / usd
    # usdEntryfee is 50
    # 2000/1 == 50/x == 0.025
    expected_entrance_fee = Web3.toWei(0.025, "ether")
    entrance_fee = lott.getEntranceFee()
    # Assert
    assert expected_entrance_fee == entrance_fee


"""
# current eth price = $2.937
# $50/2937 = 0.017 eth for 50usd
def test_get_entrance_fee():
    account = accounts[0]
    print("network.show_active() :", network.show_active())
    lottery = Lottery.deploy(
        config["networks"][network.show_active()]["eth_usd_price_feed"],
        {"from": account},
    )
    ent_fee = lottery.getEntranceFee()
    assert ent_fee > Web3.toWei(0.014, "ether")
    assert ent_fee < Web3.toWei(0.021, "ether")
"""


def test_cant_enter_unless_started():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lott = deploy_lottery()
    with pytest.raises(exceptions.VirtualMachineError):
        lott.enter({"from": get_account(), "value": lott.getEntranceFee()})


def test_can_start_and_enter_lottery():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    lott = deploy_lottery()
    account = get_account()
    lott.startLottery({"from": account})
    # Act
    lott.enter({"from": get_account(), "value": lott.getEntranceFee()})
    # Assert
    assert lott.players(0) == account


def test_can_end_lottery():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    lott = deploy_lottery()
    account = get_account()
    lott.startLottery({"from": account})

    lott.enter({"from": account, "value": lott.getEntranceFee()})
    # Act
    fund_with_link(lott)
    lott.endLottery({"from": account})
    # Assert
    assert (
        lott.lottery_state() == 2
    )  # on the array we have 0=OPEN,1=CLOSED, 2=CALCULATING_WINNER


"""

"""


def test_can_pick_winner_correctly():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    lott = deploy_lottery()  # lottery_contract
    account = get_account()
    lott.startLottery({"from": account})
    lott.enter({"from": account, "value": lott.getEntranceFee()})
    lott.enter({"from": get_account(index=1), "value": lott.getEntranceFee()})
    lott.enter({"from": get_account(index=2), "value": lott.getEntranceFee()})
    fund_with_link(lott)
    transaction = lott.endLottery({"from": account})
    request_id = transaction.events["RequestedRandomness"]["requestId"]
    # pretent we are the chainlink node

    STATIC_RNG = 777
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, STATIC_RNG, lott.address, {"from": account}
    )

    starting_balance_of_account = account.balance()
    balance_of_lottery = lott.balance()
    # 777 % 3 = 0
    assert lott.recentWinner() == account
    assert lott.balance() == 0
    assert account.balance() == starting_balance_of_account + balance_of_lottery
