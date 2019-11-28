import os
from solc import compile_files
from .data_type import SmartContract


class AsimovSolc:
    @classmethod
    def set_solidity_compiler(cls, compiler_path: str):
        """
        set solidity compiler path
        :param compiler_path: solidity compiler path
        :return:
        .. code-block:: python

            >>> from asimov import AsimovSolc
            >>> AsimovSolc.set_solidity_compiler("/usr/local/bin/solc")
        """
        os.environ['SOLC_BINARY'] = compiler_path

    @classmethod
    def compile(cls, source_file: str, **kwargs) -> dict:
        """
        compile solidity source file
        :param source_file: source file path
        :param kwargs:
        :return:

        .. code-block:: python

            >>> from asimov import AsimovSolc
            >>> c = AsimovSolc.compile("~/contracts/tutorial.sol")
            >>> c.keys()
            dict_keys(['Template', 'TemplateWarehouse', 'StringLib', 'Registry', 'Tutorial'])
            >>> type(c['Tutorial'])
            asimov.data_type.SmartContract
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

