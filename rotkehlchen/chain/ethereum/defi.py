from typing import TYPE_CHECKING, Optional

from rotkehlchen.constants.ethereum import EthereumConstants, EthereumContract
from rotkehlchen.fval import FVal
from rotkehlchen.typing import Price

if TYPE_CHECKING:
    from rotkehlchen.chain.ethereum.manager import EthereumManager


YEARN_YCRV_VAULT = EthereumConstants().contract('YEARN_YCRV_VAULT')
CURVEFI_YSWAP = EthereumConstants().contract('CURVEFI_YSWAP')
CURVEFI_PAXSWAP = EthereumConstants().contract('CURVEFI_PAXSWAP')
YEARN_DAI_VAULT = EthereumConstants().contract('YEARN_DAI_VAULT')
YEARN_YFI_VAULT = EthereumConstants().contract('YEARN_YFI_VAULT')
YEARN_ALINK_VAULT = EthereumConstants().contract('YEARN_ALINK_VAULT')
YEARN_USDT_VAULT = EthereumConstants().contract('YEARN_USDT_VAULT')
YEARN_USDC_VAULT = EthereumConstants().contract('YEARN_USDC_VAULT')
YEARN_TUSD_VAULT = EthereumConstants().contract('YEARN_TUSD_VAULT')
CURVEFI_BUSDSWAP = EthereumConstants().contract('CURVEFI_BUSDSWAP')
YEARN_BCURVE_VAULT = EthereumConstants().contract('YEARN_BCURVE_VAULT')
CURVEFI_RENSWAP = EthereumConstants().contract('CURVEFI_RENSWAP')
CURVEFI_SRENSWAP = EthereumConstants().contract('CURVEFI_SRENSWAP')
YEARN_SRENCURVE_VAULT = EthereumConstants().contract('YEARN_SRENCURVE_VAULT')
CURVEFI_SUSDV2SWAP = EthereumConstants().contract('CURVEFI_SUSDV2SWAP')
YEARN_CONTROLLER = EthereumConstants().contract('YEARN_CONTROLLER')


def _handle_yearn_curve_vault(
        ethereum: 'EthereumManager',
        curve_contract: EthereumContract,
        yearn_contract: EthereumContract,
) -> FVal:
    virtual_price = ethereum.call_contract(
        contract_address=curve_contract.address,
        abi=curve_contract.abi,
        method_name='get_virtual_price',
        arguments=[],
    )
    price_per_full_share = ethereum.call_contract(
        contract_address=yearn_contract.address,
        abi=yearn_contract.abi,
        method_name='getPricePerFullShare',
        arguments=[],
    )
    usd_value = FVal(virtual_price * price_per_full_share) / 10 ** 36
    return usd_value


def _handle_curvepool_price(ethereum: 'EthereumManager', contract: EthereumContract) -> FVal:
    virtual_price = ethereum.call_contract(
        contract_address=contract.address,
        abi=contract.abi,
        method_name='get_virtual_price',
        arguments=[],
    )
    usd_value = FVal(virtual_price) / (10 ** 18)
    return usd_value


def handle_underlying_price_yearn_vault(
        ethereum: 'EthereumManager',
        underlying_asset_price: Price,
        contract: EthereumContract,
) -> FVal:
    price_per_full_share = ethereum.call_contract(
        contract_address=contract.address,
        abi=contract.abi,
        method_name='getPricePerFullShare',
        arguments=[],
    )
    usd_value = FVal(underlying_asset_price * price_per_full_share) / 10 ** 18
    return usd_value


def handle_defi_price_query(
        ethereum: 'EthereumManager',
        token_symbol: str,
        underlying_asset_price: Optional[Price],
) -> Optional[FVal]:
    """Handles price queries for token/protocols which are queriable on-chain
    (as opposed to cryptocompare/coingecko)

    Some price queries would need the underlying asset price query which should be provided here.
    We can't query it from this module due to recursive imports between rotkehlchen/inquirer
    and rotkehlchen/chain/ethereum/defi
    """
    if token_symbol == 'yyDAI+yUSDC+yUSDT+yTUSD':
        usd_value = _handle_yearn_curve_vault(
            ethereum=ethereum,
            curve_contract=CURVEFI_YSWAP,
            yearn_contract=YEARN_YCRV_VAULT,
        )
    elif token_symbol == 'yyDAI+yUSDC+yUSDT+yBUSD':
        usd_value = _handle_yearn_curve_vault(
            ethereum=ethereum,
            curve_contract=CURVEFI_BUSDSWAP,
            yearn_contract=YEARN_BCURVE_VAULT,
        )
    elif token_symbol == 'ycrvRenWSBTC':
        usd_value = _handle_yearn_curve_vault(
            ethereum=ethereum,
            curve_contract=CURVEFI_SRENSWAP,
            yearn_contract=YEARN_SRENCURVE_VAULT,
        )
    elif token_symbol == 'yDAI+yUSDC+yUSDT+yTUSD':
        usd_value = _handle_curvepool_price(ethereum, CURVEFI_YSWAP)
    elif token_symbol == 'ypaxCrv':
        usd_value = _handle_curvepool_price(ethereum, CURVEFI_PAXSWAP)
    elif token_symbol == 'crvRenWBTC':
        usd_value = _handle_curvepool_price(ethereum, CURVEFI_RENSWAP)
    elif token_symbol == 'crvRenWSBTC':
        usd_value = _handle_curvepool_price(ethereum, CURVEFI_SRENSWAP)
    elif token_symbol == 'crvPlain3andSUSD':
        usd_value = _handle_curvepool_price(ethereum, CURVEFI_SUSDV2SWAP)
    elif token_symbol == 'yDAI+yUSDC+yUSDT+yBUSD':
        usd_value = _handle_curvepool_price(ethereum, CURVEFI_BUSDSWAP)
    elif token_symbol == 'yaLINK':
        assert underlying_asset_price
        usd_value = handle_underlying_price_yearn_vault(
            ethereum=ethereum,
            underlying_asset_price=underlying_asset_price,
            contract=YEARN_ALINK_VAULT,
        )
    elif token_symbol == 'yDAI':
        assert underlying_asset_price
        usd_value = handle_underlying_price_yearn_vault(
            ethereum=ethereum,
            underlying_asset_price=underlying_asset_price,
            contract=YEARN_DAI_VAULT,
        )
    elif token_symbol == 'yETH':
        assert underlying_asset_price
        # special handling since at the time of writing final yeth address was not known
        yeth_address = ethereum.call_contract(
            contract_address=YEARN_CONTROLLER.address,
            abi=YEARN_CONTROLLER.abi,
            method_name='vaults',
            arguments=['0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'],  # address of WETH
        )
        if yeth_address == '0x0000000000000000000000000000000000000000':
            return None
        price_per_full_share = ethereum.call_contract(
            contract_address=yeth_address,
            abi=YEARN_YFI_VAULT.abi,  # any vault abi for the priceperfullshare
            method_name='getPricePerFullShare',
            arguments=[],
        )
        usd_value = FVal(underlying_asset_price * price_per_full_share) / 10 ** 18
        return usd_value
    elif token_symbol == 'yYFI':
        assert underlying_asset_price
        usd_value = handle_underlying_price_yearn_vault(
            ethereum=ethereum,
            underlying_asset_price=underlying_asset_price,
            contract=YEARN_YFI_VAULT,
        )
    elif token_symbol == 'yUSDT':
        assert underlying_asset_price
        usd_value = handle_underlying_price_yearn_vault(
            ethereum=ethereum,
            underlying_asset_price=underlying_asset_price,
            contract=YEARN_USDT_VAULT,
        )
    elif token_symbol == 'yUSDC':
        assert underlying_asset_price
        usd_value = handle_underlying_price_yearn_vault(
            ethereum=ethereum,
            underlying_asset_price=underlying_asset_price,
            contract=YEARN_USDC_VAULT,
        )
    elif token_symbol == 'yTUSD':
        assert underlying_asset_price
        usd_value = handle_underlying_price_yearn_vault(
            ethereum=ethereum,
            underlying_asset_price=underlying_asset_price,
            contract=YEARN_TUSD_VAULT,
        )
    else:
        return None

    return usd_value