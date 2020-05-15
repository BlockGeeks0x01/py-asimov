import os
from solc import compile_files
from .data_type import SmartContract


class AsimovSolc:
    """
    The primary entry point for working with solidity compiler.
    """

    @classmethod
    def set_solidity_compiler(cls, compiler_path: str) -> None:
        """
        set solidity compiler path

        :param compiler_path: solidity compiler path

        :return: None

        .. code-block:: python

            >>> from asimov import AsimovSolc
            >>> AsimovSolc.set_solidity_compiler("/usr/local/bin/solc")
        """
        os.environ['SOLC_BINARY'] = compiler_path

    @classmethod
    def compile(cls, source_file: str, **kwargs) -> dict:
        # pylint: disable=line-too-long
        """
        compile solidity source file

        :param source_file: source file path
        :param kwargs: reference to compile_files function in `py-solc <https://github.com/ethereum/py-solc>`_ library
        :type kwargs: dict

        :return: multiple compiled contract objects in dict type

        .. code-block:: python

            >>> from asimov import AsimovSolc
            >>> AsimovSolc.compile("/path/to/my/sources/example.sol")
            {'Example': {
                'abi': [{
                    'inputs': [],
                    'payable': False,
                    'stateMutability': 'nonpayable',
                    'type': 'constructor'
                }],
                'address': None,
                'bytecode': '6080604052348015600f57600080fd5b50603580601d6000396000f3006080604052600080fd00a165627a7a72305820bf199053a6eea79c7732c9211fc200781b170db435d118cbd86d2ac117e2fa360029',
                'source': 'pragma solidity ^0.4.25;\\n'
                          '\\n'
                          'contract Example {\\n'
                          '    constructor() public {}\\n'
                          '}\\n'
                }
            }
        """
        with open(source_file) as f:
            source_code = f.read()
        compiled_objects = compile_files([source_file], output_values=('abi', 'bin', 'ast'), **kwargs)
        contracts = dict()
        for key in compiled_objects:
            contracts[key.split(':')[-1]] = SmartContract(
                source_code,
                compiled_objects[key]['abi'],
                compiled_objects[key]['bin']
            )
        return contracts
