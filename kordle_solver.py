from typing import List, Tuple
import re

ALL_LETTERS = "ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎㅏㅐㅑㅒㅓㅔㅕㅖㅗㅛㅜㅠㅡㅣ"


class KordleSolver:
    
    def __init__(self, word_list_path: str = None, option = 'original', length: int = 6):
        self.word_list: List[str] = []
        self.word_list_path: str = word_list_path
        self.length: int = length
        if option == 'original':
            # 오리지널 꼬들의 단어 리스트를 불러옴.
            self.solution_word_list = self._get_solution_list(word_list_path)
        elif option == 'custom':
            # 한국어 단어 뭉치 리스트를 불러옴.
            # TODO: word_list_path 를 뭔가 다른걸로 바꿔야 함.
            self.solution_word_list = self._get_solution_list(word_list_path)
        else:
            raise ValueError('Invalid option')
        
    
    def _get_solution_list(self, path: str) -> List[str]:
        '''Load solution word list from file'''
        with open(path, 'r') as f:
            return [line.strip() for line in f.readlines()]
        
    def update(self, guessed_word: str, result: str) -> None:
        """Updates the state with the result of a guess.

        Parameters:
            guessed_word -- The word that was guessed
            result -- A string of same length as guessed_word containing feedback codes.  Each
                char must be one of:
                'C' - Letter is correct and in the correct position
                'L' - Letter is in the word but wrong position
                'X' - Letter is not in the word
        """
        # assert: 내용이 참이 아니면 에러를 발생시키는 것.
        assert(len(guessed_word) == self.wordlen)
        assert(len(result) == self.wordlen)
        assert(re.fullmatch(r'[CLX]+', result))
        
        # 추측 단어(word)에서 각 문자(letter)의 횟수 카운트
        guess_lcounts = KordleSolver._get_letter_counts(guessed_word, True)
        # 초록색,노란색인 문자 뽑아서 횟수 카운트
        result_lcounts = { l : 0 for l in ALL_LETTERS }
        for letter, rchar in zip(guessed_word, result):
            if rchar == 'C' or rchar == 'L':
                result_lcounts[letter] += 1
        # 추측한 문자 횟수와 초록색,노란색인 문자 횟수, 전체 단어 목록에서 뽑은 문자 횟수 범위셋을 가져옴
        for letter in guess_lcounts:
            gc = guess_lcounts[letter]
            rc = result_lcounts[letter]
            crange = self.letter_counts[letter]
            assert(gc >= rc)
            # 추측한 문자 횟수가 초록색,노란색인 문자 횟수보다 많으면, 초노 문자 횟수는 곧 이번 예상 단어의 정확한 문자 횟수라고 할 수 있음.
            if gc > rc:
                crange = (rc, rc)
            # 문자 횟수의 범위는 초노 문자 횟수보단 크고, 전체 단어 목록에서의 최대 문자 횟수보단 적을것임.
            else:   
                crange = (rc, crange[1])
        # 업데이트 된 문자 횟수 범위 반영
            self.letter_counts[letter] = crange
        
        # 위치에 따른 문자 정보 업데이트
        for i, (letter, rchar) in enumerate(zip(guessed_word, result)):
            if rchar == 'C':
                # 정답인 문자 정보 반영
                self.positions[i] = set([ letter ])
            else:
                # 확실하게 정답이 아니게 된 문자 정보 반영
                self.positions[i].discard(letter)
        # 만약 최소 문자 횟수가 단어 길이와 같으면, 모든 문자를 알아낸것임.
        lbound_sum = sum(( lbound for lbound, ubound in self.letter_counts.values() ))
        if lbound_sum >= self.wordlen:
            # 모든 최대 문자 횟수를 최소 문자 횟수로 설정
            self.letter_counts = { letter : ( lbound, lbound ) for letter, (lbound, ubound) in self.letter_counts.items() }
        # 모든 문자의 위치를 아는 경우를 고려하여 위치 정보 업데이트
        # 정답이 아닌 경우에 문자를 제거하는 것도 포함 됨.
        # NOTE: 가능한 문자 조합으로 위치 정보를 고려하는 것으로 개선될 수 있음.
        for letter, (lbound, ubound) in self.letter_counts.items():
            # Count positions for which this letter is the only possibility
            # 이 문자가 이 위치에서 유일한 경우일 때의 횟수 기록
            nexclusive = sum(( 1 if letter in lset and len(lset) == 1 else 0 for lset in self.positions ))
            # 유일한 경우의 횟수와 최대 문자 횟수가 같으면
            if nexclusive >= ubound:
                # 이미 이 문자의 위치를 알아낸것이므로, 다른 위치에서 확인 안해도 됨.
                for lset in self.positions:
                    if not (letter in lset and len(lset) == 1):
                        lset.discard(letter)
        # 시도한 단어 추가
        self.tried_words.add(guessed_word)
        self.tried_word_list.append(guessed_word)
        # 현재까지의 정보를 기반으로 한 예상 정답 목록 업데이트
        self._filter_words_by_known_info(self.potential_solutions)
        # 없....어도 될듯
        # if self.hard_mode:
        #     self._filter_words_by_known_info(self.potential_guesses)
        # 예상 정답 목록 업데이트 후, 문자 횟수도 업데이트
        self.letter_counts = KordleSolver._get_letter_count_ranges_of_words(list(self.potential_solutions))
        # 예상한 단어가 맞는지 체크
        if result == 'C' * self.wordlen:
            # 단어가 맞았을 경우
            self.solved = True
            self.potential_solutions = set([ guessed_word ])

    def _filter_words_by_known_info(self, words: set[str]) -> None:
            """Removes words from the set that do not fit known information."""
            # 어떤 단어가 어떤 위치에 되고 안 되는지의 정보를 기반으로 예상 정답 목록 업데이트
            # self.positions 에 대한 정규표현식
            regex_str = ''.join([
                '[' + ''.join(list(letterset)) + ']'
                for letterset in self.positions
            ])
            rx = re.compile(regex_str)
            # 정규표현식이 일치하는 단어만 추출, 또한 최소 최대 범위에 들어가는지 체크
            def word_within_bounds(word):
                lcounts = KordleSolver._get_letter_counts(word, True)
                for letter, lcount in lcounts.items():
                    lbound, ubound = self.letter_counts[letter]
                    if not (lbound <= lcount <= ubound):
                        return False
                return True
            for word in list(words):
                if not (rx.fullmatch(word) and word not in self.tried_words and word_within_bounds(word)):
                    words.discard(word)
        
    def get_guess(self) -> str:
        # Handle constant first word(s)
        if len(self.first_word_queue):
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

    @staticmethod
    def get_word_result(guess: str, target: str) -> str:
        """Returns the result string generated by comparing a guessed word to the correct target word."""
        r_list = [ 'X' ] * len(target)
        target_lcounts = KordleSolver._get_letter_counts(target, True)
        for i, (guess_letter, target_letter) in enumerate(zip(guess, target)):
            if guess_letter == target_letter:
                r_list[i] = 'C'
                target_lcounts[target_letter] -= 1
        for i, (guess_letter, target_letter) in enumerate(zip(guess, target)):
            if guess_letter != target_letter and target_lcounts[guess_letter] > 0:
                r_list[i] = 'L'
                target_lcounts[guess_letter] -= 1
        return ''.join(r_list)
            
    def run_auto(self, target_word: str) -> int:
        """Runs the game trying to guess a given target word.  Returns the number of guesses required."""
        self.reset()
        nguesses = 0
        while True:
            nguesses += 1
            guess = self.get_guess()
            if guess == target_word: break
            res = KordleSolver.get_word_result(guess, target_word)
            #print(f'Got guess {guess} ({res}) - Updating')
            self.update(guess, res)
        return nguesses
    
    def run_interactive(solver):
        while True:
            guess = solver.get_guess()
            print('추측: ' + guess)
            if len(solver.potential_solutions) == 1:
                print('이 단어 목록에 남은 마지막 단어를 추측했습니다.')
                return
            print('Enter feedback string using letters C, L, X.  Enter ! to blacklist word.  Or, to specify the word to guess: <word> <feedback>')
            res = input('결과 (C/L/X = 정확한 위치이며 문자가 맞았을 때/문자가 포함되나 위치가 틀렸을 때/문자 없음): ')
            # If input in form <word> <result>, then submit that word as the guess with the given result
            if re.fullmatch(r'[a-z]{' + str(solver.wordlen) + '} [CXL]{' + str(solver.wordlen) + '}', res):
                parts = res.split(' ')
                print(f'Guessed {parts[0]} with result {parts[1]}')
                solver.update(parts[0], parts[1])
            elif res == '!':
                print('쓰지 않을 문자' + guess)
                solver.potential_solutions.discard(guess)
                try:
                    solver.all_solution_words.remove(guess)
                except ValueError:
                    pass
                try:
                    solver.all_guess_words.remove(guess)
                except ValueError:
                    pass

                continue
            else:
                solver.update(guess, res)
            if solver.solved:
                return
        
# 클래스 내에서 함수를 호출 할때는, self.함수명() 이렇게 호출해야함.