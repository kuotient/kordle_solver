from typing import List, Tuple, Optional, Dict
from collections import defaultdict, Counter
import re
import random

ALL_LETTERS = "ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎㅏㅑㅓㅕㅗㅛㅜㅠㅡㅣ"


class KordleSolver:
    FIRST_GUESS = 'ㅈㅣㄴㅊㅜㄹ'
    def __init__(self, 
                 solution_path: str = './testword.txt',
                 guess_path: Optional[str] = None,
                 display_option: str = 'ALL',
                 option = 'daily',
                 length: int = 6):
        
        self.length = length
        
        if option == 'daily':
            self.solution_list = self._get_word_list(solution_path)
            
        elif option == 'custom':
            self.solution_list = self._get_word_list(guess_path)
            
        self.reset()
        
    
    def _get_word_list(self, path: str) -> List[str]:
        with open(path, 'r', encoding='UTF-8') as f:
            return [word.strip() for word in f.readlines()]
        
    @staticmethod
    def _get_letter_ranges(words: List[str]) -> dict[str, tuple[int, int]]:
        letter_ranges = defaultdict(lambda: (0,0))
        
        for word in words:
            for letter, count in Counter(word).items():
                letter_range = letter_ranges[letter]
                if count < letter_range[0]:
                    letter_range = (count, letter_range[1])
                elif count > letter_range[1]:
                    letter_range = (letter_range[0], count)
                letter_ranges[letter] = letter_range
        return letter_ranges
    
    # @staticmethod
    # def _fast_score_eval(guess: str, solution: str) -> int:
    #     score = 0
    #     solution_counter = Counter(solution)
    #     for guess_
    
    def _filter_words_by_known_info(self, words: set[str]) -> None:
            """Removes words from the set that do not fit known information."""
            # 어떤 단어가 어떤 위치에 되고 안 되는지의 정보를 기반으로 예상 정답 목록 업데이트
            # self.positions 에 대한 정규표현식
            regex_str = ''.join(['[' + ''.join(list(letterset)) + ']'
                                for letterset in self.positions]
                                )
            rx = re.compile(regex_str)
            # 정규표현식이 일치하는 단어만 추출, 또한 최소 최대 범위에 들어가는지 체크
            def word_within_bounds(word):
                lcounts = Counter(word)
                for letter, lcount in lcounts.items():
                    lbound, ubound = self.letter_minmax_dict[letter]
                    if not (lbound <= lcount <= ubound):
                        return False
                return True
            for word in list(words):
                if not (rx.fullmatch(word) and word not in self.tried_words and word_within_bounds(word)):
                    words.discard(word)
    
    def reset(self):
        # NOTE: 뭔가 오류가 있음.
        # self.positions = [set(ALL_LETTERS)] * self.length
        self.positions = []
        for i in range(self.length):
            self.positions.append(set(ALL_LETTERS))
        # self.letter_counts
        self.letter_minmax_dict = KordleSolver._get_letter_ranges(self.solution_list)
        self.tried_words = set()
        self.tried_word_list = []
        self.potential_solutions = set(self.solution_list)
        self.solved = False
        
    def update(self, guess: str, result: str):
        assert(len(guess) == self.length)
        assert(len(result) == self.length)
        assert(re.fullmatch(r'[CLX]+', result))
        color_counter = defaultdict(int)
        guess_counter = Counter(guess)
        
        for letter, letter_result in zip(guess, result):
            if letter_result == 'C' or letter_result == 'L':
                color_counter[letter] += 1
        
        # 문자 Minmax 업데이트        
        for letter, letter_count in guess_counter.items():
            color_count = color_counter[letter]
            letter_minmax = self.letter_minmax_dict[letter]
            
            # 초노 갯수만큼만 문자 존재하는게 확실함.
            if letter_count > color_count:
                letter_minmax = (color_count, color_count)
            # 적어도 초노 갯수보단 문자가 많을 것임.
            else:
                letter_minmax = (color_count, letter_minmax[1])
            # 문자 minmax 업데이트
            self.letter_minmax_dict[letter] = letter_minmax
            
        # Position 업데이트
        for i, (letter, letter_result) in enumerate(zip(guess, result)):
            if letter_result == 'C':
                # NOTE: set([letter]) 써야 할듯
                self.positions[i] = set([letter])
            else:
                self.positions[i].discard(letter)
        
        min_sum = sum((min_rng for min_rng, _ in self.letter_minmax_dict.values()))
        if min_sum >= self.length:
            self.letter_minmax_dict = {letter: (min_rng, min_rng) for\
                                       letter, (min_rng, _) in\
                                       self.letter_minmax_dict.items()}
        
        # TODO: 해석 필요
        for letter, ( _ , max_rng) in self.letter_minmax_dict.items():
            nexclusive = sum((1 \
                              if letter in lset and len(lset) == 1\
                              else 0\
                              for lset in self.positions ))
            if nexclusive >= max_rng:
                for lset in self.positions:
                    if not(letter in lset and len(lset) == 1):
                        lset.discard(letter)
    
        self.tried_words.add(guess)
        self.tried_word_list.append(guess)
        # TODO: 살펴봐야 함
        self._filter_words_by_known_info(self.potential_solutions)
        self.letter_minmax_dict = KordleSolver._get_letter_ranges(list(self.potential_solutions))
        if result == 'C' * self.length:
            # 단어가 맞았을 경우
            self.solved = True
            self.potential_solutions = set([guess])
            return self.potential_solutions
        return self.potential_solutions
            
    def get_guess(self) -> str:
        # Handle constant first word(s)
        if len(self.first_word_queue):
            # TODO: 1번
            print(self.first_word_queue)
            return self.first_word_queue.pop(0)

        # 남은 예상 정답이 없을 경우
        if len(self.potential_solutions) == 0:
            raise Exception('Answer unknown')
        elif len(self.potential_solutions) <= 2:
            # 예상 단어가 단 하나 남았거나,
            # 예상 단어가 두개 남음. 어쨋거나 첫 번째 단어 반환.
            return list(self.potential_solutions)[0]

        # 남은 목록 중 최선의 단어를 뽑아야 함.
        best_word = None
        best_score = -1

        # NOTE: 너무 느릴 경우, 예상 단어 목록을 샘플링 해서 사용할 수 있음.
        # 이 경우 정확도가 살짝 떨어질 수 있음.
        for word in self.potential_guesses:
            # Assuming we use this word as our guess, determine how the potential solutions will be grouped based on the obtained info.
            # For each potential solution, get the result string that would result from trying it, and count how many of each string in each group.
            # TODO: Defaultdict 쓰기
            solution_group_counts: dict[str, int] = {}
            for potsol in self.potential_solutions:
                resstr = self._fast_word_result(word, potsol)
                solution_group_counts[resstr] = solution_group_counts.get(resstr, 0) + 1
            # We want to optimize for smallest average expected group size.
            # The probability of the solution being in a given group is dependent on the group's size, so
            # the average expected group size is the weighted average of group sizes, weighted by group size.
            avg_expected_group_size = sum(( s * s for s in solution_group_counts.values() )) / sum(( s for s in solution_group_counts.values() ))
            word_score = avg_expected_group_size
            # Add a small boost if this word is one of the possible solutions
            if word in self.potential_solutions:
                word_score -= 0.01
            # Minimize the score
            if word_score < best_score or best_score == -1:
                best_score = word_score
                best_word = word

        return best_word
        
def run(solver):
    while True:
        guess = input('추측한 단어 입력: ')
        color = input('추측한 단어의 결과 색을 입력: CLX: ')
        # guess = 'ㅇㅣㅁㅈㅓㅇ'
        # color = 'CCXCCC'
        words = solver.update(guess, color)
        print(words)
        if solver.solved:
            break
            
        
        
    

solver = KordleSolver()
run(solver)
