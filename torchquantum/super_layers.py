import torchquantum as tq
import itertools

from typing import List, Iterable

__all__ = ['SuperQuantumModule',
           'Super1QLayer',
           'Super2QLayer',
           'Super1QShareFrontLayer',
           'Super1QSingleWireLayer',
           'Super1QAllButOneLayer',
           ]


def get_combs(inset: List, n=None) -> List[List]:
    all_combs = []
    if n is None:
        # all possible combinations, with different #elements in a set
        for k in range(1, len(inset) + 1):
            all_combs.extend(list(itertools.combinations(inset, k)))
    elif isinstance(n, int):
        all_combs.extend(list(itertools.combinations(inset, n)))
    elif isinstance(n, Iterable):
        for k in n:
            all_combs.extend(list(itertools.combinations(inset, k)))

    return all_combs


class SuperQuantumModule(tq.QuantumModule):
    def __init__(self, n_wires):
        super().__init__()
        self.n_wires = n_wires
        self.sample_arch = None

    def set_sample_arch(self, sample_arch):
        self.sample_arch = sample_arch

    @property
    def arch_space(self):
        return None


class Super1QLayer(SuperQuantumModule):
    def __init__(self, op, n_wires: int, has_params=False, trainable=False):
        super().__init__(n_wires=n_wires)
        self.op = op
        self.sample_wires = None
        self.ops_all = tq.QuantumModuleList()
        for k in range(n_wires):
            self.ops_all.append(op(has_params=has_params,
                                   trainable=trainable))

    @tq.static_support
    def forward(self, q_device):
        for k in range(self.n_wires):
            if k in self.sample_arch:
                self.ops_all[k](q_device, wires=k)

    @property
    def arch_space(self):
        choices = list(range(self.n_wires))
        return get_combs(choices)


class Super2QLayer(SuperQuantumModule):
    def __init__(self, op, n_wires: int, has_params=False, trainable=False,
                 wire_reverse=False):
        super().__init__(n_wires=n_wires)
        self.op = op
        self.ops_all = tq.QuantumModuleList()

        # reverse the wires, for example from [1, 2] to [2, 1]
        self.wire_reverse = wire_reverse
        for k in range(n_wires):
            self.ops_all.append(op(has_params=has_params,
                                   trainable=trainable))

    @tq.static_support
    def forward(self, q_device):
        for k in range(self.n_wires):
            if [k, (k + 1) % self.n_wires] in self.sample_arch or \
                    [(k + 1) % self.n_wires, k] in self.sample_arch:
                wires = sorted([k, (k + 1) % self.n_wires],
                               reverse=self.wire_reverse)
                self.ops_all[k](q_device, wires=wires)

    @property
    def arch_space(self):
        choices = list(itertools.combinations(list(range(self.n_wires)), 2))
        return get_combs(choices)


class Super1QShareFrontLayer(SuperQuantumModule):
    """Share the front wires, the rest can be added"""
    def __init__(self,
                 op,
                 n_wires: int,
                 n_front_share_wires: int,
                 has_params=False,
                 trainable=False,):
        super().__init__(n_wires=n_wires)
        self.n_front_share_wires = n_front_share_wires
        self.op = op
        self.ops_all = tq.QuantumModuleList()
        for k in range(n_wires):
            self.ops_all.append(op(has_params=has_params,
                                   trainable=trainable))

    @tq.static_support
    def forward(self, q_device):
        self.q_device = q_device
        for k in range(self.n_wires):
            if k < self.sample_arch:
                self.ops_all[k](q_device, wires=k)

    @property
    def arch_space(self):
        return list(range(self.n_front_share_wires, self.n_wires + 1))


class Super1QSingleWireLayer(SuperQuantumModule):
    """Only one wire will have a gate"""
    def __init__(self,
                 op,
                 n_wires: int,
                 has_params=False,
                 trainable=False,):
        super().__init__(n_wires=n_wires)
        self.op = op
        self.ops_all = tq.QuantumModuleList()
        for k in range(n_wires):
            self.ops_all.append(op(has_params=has_params,
                                   trainable=trainable))

    @tq.static_support
    def forward(self, q_device):
        for k in range(self.n_wires):
            if k == self.sample_arch:
                self.ops_all[k](q_device, wires=k)

    @property
    def arch_space(self):
        return list(range(self.n_wires))


class Super1QAllButOneLayer(SuperQuantumModule):
    """Only one wire will NOT have the gate"""
    def __init__(self,
                 op,
                 n_wires: int,
                 has_params=False,
                 trainable=False,):
        super().__init__(n_wires=n_wires)
        self.op = op
        self.ops_all = tq.QuantumModuleList()
        for k in range(n_wires):
            self.ops_all.append(op(has_params=has_params,
                                   trainable=trainable))

    @tq.static_support
    def forward(self, q_device):
        for k in range(self.n_wires):
            if k != self.sample_arch:
                self.ops_all[k](q_device, wires=k)

    @property
    def arch_space(self):
        return list(range(self.n_wires))