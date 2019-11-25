import os
from solc import compile_files
from .data_type import SmartContract


class AsimovSolc:
    @classmethod
    def set_solidity_compiler(cls, compiler_path: str):
        os.environ['SOLC_BINARY'] = compiler_path

    @classmethod
    def compile(cls, source_file: str, **kwargs) -> dict:
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

