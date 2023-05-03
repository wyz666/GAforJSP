import random
import operator
import copy
import sys

"""
Job0:Task0(3h)->Task1(4h)
Job1:Task0(2h)->Task1(3h)->Task2(4h)
Job2:Task0(4h)->Task1(5h)->Task2(2h)
M0:(0,0),(1,1),(2,0)
M1:(1,2),(2,1)
M2:(0,1),(1,0),(2,2)
"""


class Task(object):
    """工序类"""

    def __init__(self, job_id, task_id, machine_id, duration):
        self.job_id = job_id
        self.task_id = task_id
        self.machine_id = machine_id
        self.duration = duration
        self.start_time = None
        self.end_time = None
        self.scheduled = None

    def calc_end_time(self):
        self.end_time = self.start_time + self.duration


class Chromosome:
    """种群个体"""

    def __init__(self, unsolved_job_nodes, shuffled_mac_nodes):
        self.solution = unsolved_job_nodes
        self.permutation = shuffled_mac_nodes
        self.fun = None
        self.eval = None
        self.result = None


def create_task_list(tasks, str):
    """根据输入tasks，创建job和machine列表"""
    if str == "job":
        # 根据输入确定有几个job
        job_num = 0
        for t in tasks:
            if job_num < t.job_id:
                job_num = t.job_id
        # 创建2维列表
        job_list = []
        for i in range(job_num + 1):
            job_list.append([])
        for t in tasks:
            job_list[t.job_id].append(t)
        for j in job_list:
            sort_attr = operator.attrgetter("task_id")  # 根据Task类中的task_id属性排序
            j.sort(key=sort_attr)
        return job_list

    if str == "machine":
        mac_num = 0
        for t in tasks:
            if mac_num < t.machine_id:
                mac_num = t.machine_id
        mac_list = []
        for i in range(mac_num + 1):
            mac_list.append([])
        for t in tasks:
            mac_list[t.machine_id].append(t)
        return mac_list


def init_population(job_nodes, machine_nodes, population_num):
    """初始化种群"""
    population = []
    for i in range(population_num):
        for machine in machine_nodes:
            random.shuffle(machine)  # 每台机器打乱排序

        deepcopy_nodes = copy.deepcopy(machine_nodes)  # 深拷贝，后续操作不受原对象影响
        # for m in machine_nodes:
        #     for t in m:
        #         print("(%d, %d) " % (t.job_id, t.task_id), end=" ")
        #     print(end="| ")
        # print()
        chromosome = Chromosome(job_nodes, deepcopy_nodes)

        population.append(chromosome)

    return population


def calc_fun(chromosome):
    """计算目标函数"""
    solution = get_solution(chromosome.solution, chromosome.permutation)
    # show_solution(solution)
    chromosome.fun = process_end_time(solution)
    chromosome.result = process_end_time(solution)
    # print(chromosome.makespan)


def get_solution(job_nodes, machine_nodes):
    machine_available_time_record = [0] * len(machine_nodes)  # 初始化机器状态
    earliest_tasks = []  # 可执行工序集
    for j in job_nodes:
        for t in j:
            t.scheduled = False  # 初始化调用状态
            if t.task_id == 0:
                earliest_tasks.append(t)  # task_id为0代表每个job的第一个工序，这个列表里存放的是前置节点都完成的工序

    # 主循环，选择工序，赋予工时
    #
    #######################问题#############################
    while earliest_tasks:
        random.shuffle(earliest_tasks)  # 不打乱每次执行的排序是相同的，这也是编码出问题的原因
        selected_task = None
        for e_t in earliest_tasks:  # 每次从集合里选择第一个工序
            if selected_task:
                break
            for m in machine_nodes:
                for t in m:
                    if t.scheduled:
                        continue
                    if e_t.job_id == t.job_id and e_t.task_id == t.task_id:
                        selected_task = t
                        break

        if selected_task:
            previous_task_end_time = 0  # 工序前置节点结束时间
            if selected_task.task_id:
                previous_task_end_time = job_nodes[selected_task.job_id][selected_task.task_id - 1].end_time
            machine_available_time = machine_available_time_record[selected_task.machine_id]  # 工序所需机器可用时间
            job_nodes[selected_task.job_id][selected_task.task_id].start_time = max(previous_task_end_time,
                                                                                    machine_available_time)
            job_nodes[selected_task.job_id][selected_task.task_id].calc_end_time()
            job_nodes[selected_task.job_id][selected_task.task_id].scheduled = True
            machine_available_time_record[selected_task.machine_id] = \
                job_nodes[selected_task.job_id][selected_task.task_id].end_time
            earliest_tasks.remove(job_nodes[selected_task.job_id][selected_task.task_id])
            if selected_task.task_id < len(job_nodes[selected_task.job_id]) - 1:
                earliest_tasks.append(job_nodes[selected_task.job_id][selected_task.task_id + 1])
    return job_nodes


def process_end_time(solution_nodes):
    process_end_time = 0
    for job in solution_nodes:
        for t in job:
            if t.end_time > process_end_time:
                process_end_time = t.end_time
    return process_end_time


def calc_eval(generation, last_zeta):
    if last_zeta:
        zeta = 0.9 * last_zeta
    else:
        zeta = 10
    longest_process_time = 0
    for c in generation:
        calc_fun(c)
        print(c.fun, end=" ")
        if c.fun > longest_process_time:
            longest_process_time = c.fun
    print()
    sum_fun = 0
    for c in generation:
        c.fun = longest_process_time - c.fun + zeta
        # print(c.fun,end=" ")
        sum_fun += c.fun
    for c in generation:
        c.eval = c.fun / sum_fun
    return zeta


def cross(generation, cross_rate):
    parents_index = []
    for i in range(len(generation)):
        # for j in c.permutation:
        #     for t in j:
        #         print("(%d, %d) " % (t.job_id, t.task_id), end=" ")
        #     print(end="| ")
        # print()
        if random.random() < cross_rate:
            parents_index.append(i)

    # for c in parents:
    # for j in c.permutation:
    #     for t in j:
    #         print("(%d, %d) " % (t.job_id, t.task_id), end=" ")
    #     print(end="| ")
    # print()
    if len(parents_index) % 2 != 0:
        parents_index.pop()
    i = 0
    while i < len(parents_index):
        child_per1 = get_child_permutation(generation[parents_index[i]], generation[parents_index[i + 1]])
        child_per2 = get_child_permutation(generation[parents_index[i + 1]], generation[parents_index[i]])
        generation[parents_index[i]].permutation = child_per1
        generation[parents_index[i + 1]].permutation = child_per2
        i += 2
    # for c in parents:
    #     for j in c.permutation:
    #         for t in j:
    #             print("(%d, %d) " % (t.job_id, t.task_id), end=" ")
    #         print(end="| ")
    #     print()
    return generation


def get_child_permutation(fa, ma):
    child_permutation = []
    mac_num = len(fa.permutation)
    for i in range(mac_num):
        child_permutation.append([])
    # print("fa")
    # for j in fa.permutation:
    #     for t in j:
    #         print("(%d, %d) " % (t.job_id, t.task_id), end=" ")
    #     print(end="| ")
    # print()
    # print("ma")
    # for j in ma.permutation:
    #     for t in j:
    #         print("(%d, %d) " % (t.job_id, t.task_id), end=" ")
    #     print(end="| ")
    # print()

    for mac_i in range(mac_num):
        task_num = len(fa.permutation[mac_i])
        cross_index = random.randint(0, task_num - 1)
        # print(cross_index)
        selected_nodes = copy.deepcopy(fa.permutation[mac_i][cross_index:])
        for child_i in range(task_num):
            if child_i < cross_index:
                for ma_t in ma.permutation[mac_i]:
                    exist = False
                    for se_t in selected_nodes:
                        if se_t.job_id == ma_t.job_id and se_t.task_id == ma_t.task_id:
                            exist = True
                            break
                    if not exist:
                        child_permutation[mac_i].append(ma_t)
                        selected_nodes.append(ma_t)
                        break
            else:
                child_permutation[mac_i].append(fa.permutation[mac_i][child_i])

    # for j in child_permutation:
    #     for t in j:
    #         print("(%d, %d) " % (t.job_id, t.task_id), end=" ")
    #     print(end="| ")
    # print()
    return child_permutation


def mutate(generation, mutate_rate):
    # for c in generation:
    #     for j in c.permutation:
    #         for t in j:
    #             print("(%d, %d) " % (t.job_id, t.task_id), end=" ")
    #         print(end="| ")
    #     print()
    for c in generation:
        if random.random() < mutate_rate:
            mutate_id = random.randint(0, len(c.permutation) - 1)
            # print(mutate_id)
            c.permutation[mutate_id].reverse()
    # for c in generation:
    #     for j in c.permutation:
    #         for t in j:
    #             print("(%d, %d) " % (t.job_id, t.task_id), end=" ")
    #         print(end="| ")
    #     print()
    return generation


def get_best_chromosome(generation):
    best_eval = 0
    gen_best_chromosome = None
    for c in generation:
        if c.eval > best_eval:
            best_eval = c.eval
            gen_best_chromosome = c

    return gen_best_chromosome


def select(generation):
    next_generation = []
    gen_len = len(generation)
    for next_generation_i in range(gen_len):
        competitors = []
        for competitors_i in range(3):
            competitors.append(generation[random.randint(0, gen_len - 1)])
        max_eval_in_competitors = 0
        best_competitor = None
        for c in competitors:
            if c.eval > max_eval_in_competitors:
                max_eval_in_competitors = c.eval
                best_competitor = c
        next_generation.append(best_competitor)

    return next_generation


def show_solution(solution):
    for j in solution:
        for t in j:
            print("(%d，%d，m%d，开始：%d，结束：%d) " % (t.job_id, t.task_id, t.machine_id, t.start_time, t.end_time), end=" ")
        print(end="| ")
    print()


def show_permutation(permutation):
    for m in permutation:
        for t in m:
            print("(%d, %d) " % (t.job_id, t.task_id), end=" ")
        print(end="| ")
    print()


if __name__ == '__main__':
    # 输入问题
    enter_tasks = [Task(0, 1, 2, 4), Task(0, 0, 0, 3),
                   Task(1, 0, 2, 2), Task(1, 1, 0, 3), Task(1, 2, 1, 4),
                   Task(2, 0, 0, 4), Task(2, 1, 1, 5), Task(2, 2, 2, 2)]
    # 创建二维数组
    job_task = create_task_list(enter_tasks, "job")
    machine_task = create_task_list(enter_tasks, "machine")
    # for j in job_task:
    #     for t in j:
    #         print("(%d, %d) " % (t.job_id, t.task_id), end=" ")
    #     print()

    best_chromosome = None  # 记录最佳个体
    best_result = sys.maxsize  # 记录最佳结果
    population = init_population(job_task, machine_task, 10)  # 初始化种群
    for i in range(10000):  # 开始种群迭代
        print("---------------第%d代---------------" % (i + 1))
        population_c = cross(population, 0.95)  # 交叉
        population_c_m = mutate(population_c, 0.1)  # 变异
        calc_eval(population_c_m, None)  # 计算目标函数以及个体适应度
        # 比较本代最佳个体与历史最优个体
        gen_best_chromosome = get_best_chromosome(population_c_m)
        if best_result > gen_best_chromosome.result:
            best_chromosome = copy.deepcopy(gen_best_chromosome)
            best_result = best_chromosome.result
        # print("本代最短工时：%d" % gen_best_chromosome.result)
        # print("当前最短工时：%d" % best_result)
        # print("当前最佳方案：")
        # show_permutation(best_chromosome.permutation)
        # show_solution(best_chromosome.solution)
        population = select(population_c_m)  # 选择出下一代
