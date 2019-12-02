import json
from typing import Union
from web3 import Web3
import eth_abi
from .data_type import EvmLog, EvmLogs


# https://codeburst.io/deep-dive-into-ethereum-logs-a8d2047c7371
class EvmLogParser:
    """
    The primary entry point for working with Asimov smart contract execution logs.
    """

    @classmethod
    def parse(cls, raw_log: Union[dict, list], abi: Union[dict, str]) -> EvmLogs:
        """
        Parse asimov vm execution log

        :param raw_log: contract execution log
        :param abi: contract abi object in json format
        :return: parsed log list
        """
        if isinstance(abi, str):
            abi = json.loads(abi)
        if type(raw_log) is dict:
            raw_logs = [raw_log]
        else:
            raw_logs = raw_log

        events = [e for e in abi if e['type'] == 'event']
        events_hash = {}
        for event in events:
            signature = Web3.sha3(text=f"{event['name']}({','.join([_input['type'] for _input in event['inputs']])})")
            events_hash[signature.hex()] = event
        logs = EvmLogs()
        for _raw_log in raw_logs:
            log = EvmLog(_raw_log)
            event_abi = events_hash[log.topics[0]]
            indexed_types = [e['type'] for e in event_abi['inputs'] if e['indexed']]
            indexed_names = [e['name'] for e in event_abi['inputs'] if e['indexed']]
            types = [e['type'] for e in event_abi['inputs'] if not e['indexed']]
            names = [e['name'] for e in event_abi['inputs'] if not e['indexed']]
            indexed_values = [eth_abi.decode_single(t, Web3.toBytes(hexstr=v)) for t, v in zip(indexed_types, log.topics[1:])]
            values = list(eth_abi.decode_abi(types, Web3.toBytes(hexstr=log.data)))
            logs.append({
                "name": event_abi['name'],
                "args": {n: v for n, v in zip(names + indexed_names, values + indexed_values)}
            })
        return logs
