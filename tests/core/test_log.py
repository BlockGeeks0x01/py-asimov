from asimov import AsimovSolc, EvmLogParser


def test_vm_log():
    abi = AsimovSolc.compile('tests/fixtures/Refund.sol')['Refund'].abi
    receipt = {'root': '0xffe093d1ec60e65b488eb06addd1beca04aff0998ee77656bb9f7e808c9090ce', 'status': '0x1',
               'cumulativeGasUsed': '0x0',
               'logsBloom': '0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002040000000000000400000000100000000000000000000000000000000000008000000000000001000000420000000000000000000800000000000000000100000000000000000000000000000000000000000000010200000000000000000410000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000002000000000000000000000020080000000000000020800000000000000000000000000000000000000000000000040000000000000000',
               'logs': [{'address': '0x639195a77e67bba57c4dee0eb90fa69c382af32068',
                         'topics': ['0x969b7dfe904e12379ac05bce497fa9088da9fa8df26ff2a80040a606b4327e77'],
                         'data': '0x000000000000000000000066147fa5db10fb56cdf5911304efc2a3e59c39ca68000000000000000000000000000000000000000000000000000000003b9aca000000000000000000000000000000000000000000000000000000000000000000',
                         'blockNumber': '0x688f',
                         'transactionHash': '0bb3b39e71a8b585ccd2c7398d5cd1f6b268c1f5ba9bfc42c434be78734cea3e',
                         'transactionIndex': '0x2',
                         'blockHash': '2db1bdaa9ecc71a6ea9e077ebd0e68f6aceea2ca5c6f44066d559f6f7b8f681d',
                         'logIndex': '0x0', 'removed': False},
                        {'address': '0x639195a77e67bba57c4dee0eb90fa69c382af32068',
                         'topics': ['0xfb6314fe8815b6ca7b5804da14bb460b9d07aa5c682d4a46b06e38a5367de2b0',
                                    '0x000000000000000000000066147fa5db10fb56cdf5911304efc2a3e59c39ca68',
                                    '0x000000000000000000000000000000000000000000000000000000003b9aca00',
                                    '0x0000000000000000000000000000000000000000000000000000000000000000'], 'data': '0x',
                         'blockNumber': '0x688f',
                         'transactionHash': '0bb3b39e71a8b585ccd2c7398d5cd1f6b268c1f5ba9bfc42c434be78734cea3e',
                         'transactionIndex': '0x2',
                         'blockHash': '2db1bdaa9ecc71a6ea9e077ebd0e68f6aceea2ca5c6f44066d559f6f7b8f681d',
                         'logIndex': '0x1', 'removed': False},
                        {'address': '0x639195a77e67bba57c4dee0eb90fa69c382af32068',
                         'topics': ['0x03b2212fb69fba773f7a7d89e4859394969c7589648cb9306892e07ba680a4dd',
                                    '0x000000000000000000000000000000000000000000000000000000003b9aca00'],
                         'data': '0x000000000000000000000066147fa5db10fb56cdf5911304efc2a3e59c39ca680000000000000000000000000000000000000000000000000000000000000000',
                         'blockNumber': '0x688f',
                         'transactionHash': '0bb3b39e71a8b585ccd2c7398d5cd1f6b268c1f5ba9bfc42c434be78734cea3e',
                         'transactionIndex': '0x2',
                         'blockHash': '2db1bdaa9ecc71a6ea9e077ebd0e68f6aceea2ca5c6f44066d559f6f7b8f681d',
                         'logIndex': '0x2', 'removed': False}],
               'transactionHash': '0bb3b39e71a8b585ccd2c7398d5cd1f6b268c1f5ba9bfc42c434be78734cea3e',
               'contractAddress': '0x000000000000000000000000000000000000000000', 'gasUsed': '0x0'}
    logs = EvmLogParser.parse(receipt['logs'], abi)
    assert logs[0]['name'] == 'ReceiveMoney'
    assert logs[1]['name'] == 'IndexReceiveMoney'
    assert logs[2]['name'] == 'PartialIndexReceiveMoney'
