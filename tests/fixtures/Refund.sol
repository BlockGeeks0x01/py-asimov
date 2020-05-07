pragma solidity ^0.4.25;

contract Refund {
    uint public count;
    constructor() public {}
    event ReceiveMoney(address sender, uint value, uint asset_type);
    event IndexReceiveMoney(address indexed sender, uint indexed value, uint indexed asset_type);
    event PartialIndexReceiveMoney(address sender, uint indexed value, uint asset_type);

    function() external payable {
        count += 1;
        emit ReceiveMoney(msg.sender, msg.value, msg.assettype);
        emit IndexReceiveMoney(msg.sender, msg.value, msg.assettype);
        emit PartialIndexReceiveMoney(msg.sender, msg.value, msg.assettype);
    }

    function send() external payable {
        count += 1;
        msg.sender.transfer(msg.value, msg.assettype);
    }

    function withdraw(uint value) public {
        msg.sender.transfer(value * 1e8, 0x000000000000000000000000);
    }

    function withdraw() public {
        msg.sender.transfer(1 * 1e8, 0x000000000000000000000000);
    }
}
