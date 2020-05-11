pragma solidity ^0.4.25;

library StringLib {

    /// @dev convert address to string
    /// @param x the address to covert
    function convertAddrToStr(address x) internal pure returns (string) {
        bytes memory b = new bytes(20);
        for (uint i = 0; i < 20; i++)
            b[i] = byte(uint8(uint(x) / (2**(8*(19 - i)))));
        return string(b);
    }

    /// @dev concat two strings
    /// @param _a the first string
    /// @param _b the second string
    function strConcat(string _a, string _b) internal pure returns (string) {
        bytes memory _ba = bytes(_a);
        bytes memory _bb = bytes(_b);

        string memory ab = new string(_ba.length + _bb.length);
        bytes memory bab = bytes(ab);
        uint k = 0;
        for (uint i = 0; i < _ba.length; i++) bab[k++] = _ba[i];
        for (i = 0; i < _bb.length; i++) bab[k++] = _bb[i];

        return string(bab);
    }

}

interface TemplateWarehouse{
    function getTemplate(uint16 _category, string name) external returns(string, bytes, uint, uint8, uint8, uint8, uint16);
}

/// @title This is the base contract any other contracts must directly or indirectly inherit to run on Asimov platform
///  Asimov only accepts a template rather than a randomly composed Solidity contract
///  An Asimov template always belongs to a given category and has a unique template name in the category
contract Template {
    /// @dev should set to private to improve security SECURITY ISSUE!
    uint16 internal category;
    string internal templateName;

    bool initialized = false;

    /// @dev initialize a template
    ///  it was originally the logic inside the constructor
    ///  it is changed in such way to provide a better user experience in the Asimov debugging tool
    /// @param _category category of the template
    /// @param _templateName name of the template
    function initTemplate(uint16 _category, string _templateName) public {
        require(!initialized);
        category = _category;
        templateName = _templateName;
        initialized = true;
    }

    /// @dev get the template information
    function getTemplateInfo() public view returns (uint16, string){
        return (category, templateName);
    }

}

contract Refund is Template {
    uint public count;
    mapping (uint => address) public dict;
    constructor() public {}
    event callParseLog(address sender);
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

    function parseLog() public {
        emit callParseLog(msg.sender);
    }
}
